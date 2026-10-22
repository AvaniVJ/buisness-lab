from pydantic import BaseModel, Field, HttpUrl
from typing import Literal

class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=12)

class Source(BaseModel):
    title: str
    url: HttpUrl
    relevance: float
    excerpt: str

class QueryResponse(BaseModel):
    answer: str
    status: Literal["answered", "insufficient_evidence"]
    sources: list[Source]
    needs_human: bool

class ExpertAnswerRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    answer: str = Field(min_length=3, max_length=10000)
    source_url: HttpUrl | None = None
    reviewer: str = Field(min_length=1, max_length=200)
