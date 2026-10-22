from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from . import db
from .config import settings
from .schemas import QueryRequest, ExpertAnswerRequest
from .knowledge import answer_question
from .ingestion import run_ingestion
from . import db as database

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield

app=FastAPI(title=settings.app_name, version="0.1.0",
            description="Reusable product knowledge API for support and consulting agents.",
            lifespan=lifespan)

@app.get("/health")
def health():
    return {"status":"ok","service":settings.app_name}

@app.post("/query")
def query(request: QueryRequest):
    try:
        return answer_question(request.question,request.top_k)
    except Exception as exc:
        raise HTTPException(status_code=503,detail=f"Knowledge query failed: {type(exc).__name__}")

@app.post("/ingestion/run")
async def ingestion_run():
    try:
        return await run_ingestion()
    except Exception as exc:
        raise HTTPException(status_code=502,detail=f"Ingestion failed: {type(exc).__name__}: {str(exc)[:250]}")

@app.get("/ingestion/status")
def ingestion_status():
    return database.run_status()

@app.get("/escalations")
def list_escalations():
    from .db import connect
    with connect() as conn:
        rows=conn.execute("SELECT id,question,reason,created_at,status FROM escalations ORDER BY id DESC LIMIT 100").fetchall()
        return {"items":[dict(r) for r in rows]}

@app.post("/escalations/{escalation_id}/resolve")
def resolve_escalation(escalation_id: int, request: ExpertAnswerRequest):
    ok=database.resolve_escalation(escalation_id,request.answer,request.reviewer,
                                   str(request.source_url) if request.source_url else None)
    if not ok:
        raise HTTPException(status_code=404,detail="Escalation not found")
    return {"status":"resolved","escalation_id":escalation_id,"knowledge_added":True}
