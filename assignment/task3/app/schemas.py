from pydantic import BaseModel, Field
from typing import Literal

class TranscriptRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=100)
    transcript: str = Field(min_length=30, max_length=200000)
    meeting_label: str = Field(default="initial", max_length=100)
    approved_baseline_id: int | None = None

class Requirement(BaseModel):
    requirement_id: str
    description: str
    status: Literal["confirmed", "unclear", "disputed"]
    priority: Literal["must_have", "should_have", "optional"]
    evidence: str
    acceptance_criteria: list[str]
    assumptions: list[str]
    dependencies: list[str]
    feasibility: Literal["existing_configuration", "existing_with_limitations", "potential_custom_development", "needs_clarification"] = "needs_clarification"
    knowledge_sources: list[str] = []
    estimate_low_hours: float = 0
    estimate_likely_hours: float = 0
    estimate_high_hours: float = 0

class AnalysisResponse(BaseModel):
    project_id: str
    meeting_label: str
    requirements: list[Requirement]
    open_questions: list[str]
    risks: list[str]
    assumptions: list[str]

class ReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=200)
    approved: bool
    notes: str = ""
