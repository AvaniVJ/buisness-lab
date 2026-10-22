from contextlib import asynccontextmanager
import json
from fastapi import FastAPI, HTTPException
from . import db
from .schemas import TranscriptRequest, ReviewRequest
from .agents import analyse_transcript, check_feasibility, estimate_work, create_scope, create_proposal, compare_to_baseline

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield

app=FastAPI(title="Meeting to Scope",version="0.1.0",
 description="Turns meeting transcripts into requirements, estimates and proposal drafts.",lifespan=lifespan)

@app.get("/health")
def health():
    return {"status":"ok","service":"meeting-to-scope"}

@app.post("/projects/analyse")
async def analyse(request: TranscriptRequest):
    try:
        analysis=await analyse_transcript(request.project_id,request.meeting_label,request.transcript)
        analysis=await check_feasibility(analysis)
        estimate=estimate_work(analysis)
        scope=create_scope(analysis,estimate)
        proposal=create_proposal(request.project_id,scope,estimate)
        meeting_id=db.save_meeting(request.project_id,request.meeting_label,request.transcript,analysis)
        baseline_id=db.save_baseline(request.project_id,analysis,scope,estimate,proposal)
        changes=None
        if request.approved_baseline_id:
            baseline=db.get_baseline(request.approved_baseline_id)
            if not baseline or baseline["project_id"]!=request.project_id or not baseline["approved"]:
                raise HTTPException(status_code=400,detail="Baseline must exist, belong to this project, and be human-approved.")
            changes=compare_to_baseline(analysis,json.loads(baseline["analysis_json"]))
        return {"meeting_id":meeting_id,"baseline_id":baseline_id,"project_id":request.project_id,
                "analysis":analysis,"scope":scope,"estimate":estimate,"proposal":proposal,
                "changes":changes,"approval_status":"pending_human_approval"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502,detail=f"Analysis failed: {type(exc).__name__}: {str(exc)[:300]}")

@app.get("/projects/{project_id}/baselines")
def baselines(project_id: str):
    return {"items":db.list_baselines(project_id)}

@app.get("/baselines/{baseline_id}")
def get_baseline(baseline_id: int):
    row=db.get_baseline(baseline_id)
    if not row: raise HTTPException(status_code=404,detail="Baseline not found")
    for key in ("analysis_json","scope_json","estimate_json","proposal_json"):
        row[key.replace("_json","")]=json.loads(row.pop(key))
    return row

@app.post("/baselines/{baseline_id}/review")
def review(baseline_id: int, request: ReviewRequest):
    if not db.review_baseline(baseline_id,request.reviewer,request.approved,request.notes):
        raise HTTPException(status_code=404,detail="Baseline not found")
    return {"baseline_id":baseline_id,"approved":request.approved,
            "message":"Only approved baselines can be used for future change comparisons."}
