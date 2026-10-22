import json, re
from typing import Any
import anthropic
from .config import settings
from .knowledge_client import query_brain

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None

def _extract_json(text: str) -> dict:
    cleaned=re.sub(r"^```(?:json)?\s*|\s*```$","",text.strip(),flags=re.I)
    return json.loads(cleaned)

def _claude(system: str, user: str, max_tokens: int=3500) -> dict:
    if _client is None:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")
    response=_client.messages.create(model=settings.claude_model,max_tokens=max_tokens,system=system,
                                     messages=[{"role":"user","content":user}])
    text="".join(b.text for b in response.content if getattr(b,"type",None)=="text")
    return _extract_json(text)

async def analyse_transcript(project_id: str, meeting_label: str, transcript: str) -> dict:
    # Staged extraction keeps long transcripts manageable and preserves passage evidence.
    sections=[transcript[i:i+12000] for i in range(0,len(transcript),10500)]
    extracted=[]
    for index, section in enumerate(sections, start=1):
        result=_claude(
            "You are a transcript analyst. Extract only requirements, decisions, constraints, commitments, unresolved questions and risks explicitly supported by this transcript segment. Preserve short verbatim evidence quotes. Do not infer agreement from brainstorming. Return JSON with keys requirements, open_questions, risks, assumptions. Each requirement: description, status (confirmed/unclear/disputed), priority (must_have/should_have/optional), evidence, acceptance_criteria, assumptions, dependencies.",
            f"Project: {project_id}; meeting: {meeting_label}; segment {index}/{len(sections)}\nTranscript segment:\n{section}", 3000)
        extracted.append({"segment":index,**result})
    merged=_claude(
        "You are a senior requirements analyst. Merge extracted transcript evidence, deduplicate requirements, preserve uncertainty and conflicts, and do not invent commitments. Assign stable IDs REQ-001 etc. Return JSON with keys requirements, open_questions, risks, assumptions. Each requirement must include requirement_id, description, status, priority, evidence, acceptance_criteria, assumptions, dependencies.",
        json.dumps({"project_id":project_id,"meeting_label":meeting_label,"segments":extracted},ensure_ascii=False), 4000)
    merged["project_id"]=project_id
    merged["meeting_label"]=meeting_label
    # Normalize required fields for downstream code.
    for i, req in enumerate(merged.get("requirements",[]),1):
        req.setdefault("requirement_id",f"REQ-{i:03d}")
        req.setdefault("status","unclear")
        req.setdefault("priority","should_have")
        req.setdefault("evidence","")
        req.setdefault("acceptance_criteria",[])
        req.setdefault("assumptions",[])
        req.setdefault("dependencies",[])
        req["feasibility"]="needs_clarification"
        req["knowledge_sources"]=[]
        req["estimate_low_hours"]=0
        req["estimate_likely_hours"]=0
        req["estimate_high_hours"]=0
    return merged

async def check_feasibility(analysis: dict) -> dict:
    for req in analysis.get("requirements",[]):
        try:
            kb=await query_brain(req["description"])
            req["knowledge_sources"]=[s.get("url","") for s in kb.get("sources",[])]
            prompt=_claude(
                "You are a product feasibility analyst. Use only the Knowledge Brain result. Choose exactly one feasibility label: existing_configuration, existing_with_limitations, potential_custom_development, needs_clarification. A missing search result is not proof that a feature does not exist. Return JSON {feasibility, rationale, questions}.",
                json.dumps({"requirement":req["description"],"knowledge":kb},ensure_ascii=False), 700)
            req["feasibility"]=prompt.get("feasibility","needs_clarification")
            req["feasibility_rationale"]=prompt.get("rationale","")
            req["feasibility_questions"]=prompt.get("questions",[])
        except Exception as exc:
            req["feasibility"]="needs_clarification"
            req["feasibility_rationale"]="Knowledge Brain unavailable; no claim about product capability can be made."
            req["feasibility_questions"]=["Ask a product expert to verify this requirement."]
    return analysis

def estimate_work(analysis: dict) -> dict:
    requirements=analysis.get("requirements",[])
    # Claude estimates effort with ranges and assumptions, not a contractual commitment.
    result=_claude(
        "You are a cautious software estimation engineer. Estimate work only from the structured requirements. Return JSON {tasks:[{requirement_id,task,low_hours,likely_hours,high_hours,assumptions,dependencies}], total_low_hours,total_likely_hours,total_high_hours,risks}. Use nonnegative numeric hours. Existing configuration may need less effort than custom work. If detail is missing, widen the range and state assumptions. Estimates are planning ranges, not commitments.",
        json.dumps({"requirements":requirements},ensure_ascii=False), 3000)
    for task in result.get("tasks",[]):
        for key in ("low_hours","likely_hours","high_hours"):
            try: task[key]=max(0,float(task[key]))
            except (TypeError,ValueError): task[key]=0
        task["high_hours"]=max(task["high_hours"],task["likely_hours"])
        task["likely_hours"]=max(task["likely_hours"],task["low_hours"])
    result["currency"]=settings.currency
    result["hourly_rate"]=settings.hourly_rate
    result["price_range"]={
        "low":round(float(result.get("total_low_hours",0))*settings.hourly_rate,2),
        "likely":round(float(result.get("total_likely_hours",0))*settings.hourly_rate,2),
        "high":round(float(result.get("total_high_hours",0))*settings.hourly_rate,2)}
    return result

def create_scope(analysis: dict, estimate: dict) -> dict:
    return _claude(
        "You are a senior technical consultant. Create a concise scope of work from requirements and estimates. Separate confirmed requirements, assumptions, exclusions, dependencies, acceptance criteria, client responsibilities, risks and open questions. Never present uncertain requirements as agreed. Return JSON with keys objective, deliverables, exclusions, assumptions, dependencies, acceptance_criteria, client_responsibilities, risks, open_questions.",
        json.dumps({"analysis":analysis,"estimate":estimate},ensure_ascii=False), 2500)

def create_proposal(project_id: str, scope: dict, estimate: dict) -> dict:
    return _claude(
        "You are a client proposal writer. Create a clear proposal draft consistent with the scope and estimate. Do not invent dates, tax treatment, payment terms, or guarantee delivery. Mark unconfirmed details as placeholders. Return JSON with keys executive_summary, proposed_solution, deliverables, timeline_assumptions, effort_and_price, exclusions, dependencies, risks, approval_required.",
        json.dumps({"project_id":project_id,"scope":scope,"estimate":estimate},ensure_ascii=False), 2200)

def compare_to_baseline(new_analysis: dict, baseline_analysis: dict) -> dict:
    return _claude(
        "You are a scope-change analyst. Compare the new meeting requirements against the APPROVED baseline requirements. Classify each change as added, modified, removed, unchanged, or needs_clarification. Flag work not in baseline as potentially out of scope; do not assert extra charges without human approval. Return JSON {changes:[{requirement_id,change_type,description,baseline_evidence,new_evidence,scope_impact,needs_requote}],summary,open_questions}.",
        json.dumps({"approved_baseline":baseline_analysis,"new_meeting":new_analysis},ensure_ascii=False), 2500)
