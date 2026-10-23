from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class Citation(BaseModel):
    """Citation referencing an actual passage in the source document."""
    source: str = Field(..., description="Source document filename (e.g., designs_manual.pdf)")
    page: int = Field(..., description="1-indexed PDF page number in the original document")
    section: str = Field(..., description="Verified chapter or section title identified in document text")
    excerpt: str = Field(..., description="Supporting excerpt extracted directly from the source chunk")

class AskRequest(BaseModel):
    """Incoming user question request."""
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The question regarding Indian industrial design registration"
    )

    @field_validator("question")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty or only whitespace.")
        return cleaned

class AskResponse(BaseModel):
    """Response returned to the user or API client."""
    question: str
    answer: str = Field(..., description="Grounded answer or exact 'Not found'")
    found: bool = Field(..., description="True if answer is grounded in retrieved source evidence, False otherwise")
    citations: List[Citation] = Field(default_factory=list, description="List of verified citations from retrieved chunks")

class HealthResponse(BaseModel):
    """System health and operational status."""
    status: str
    database_initialized: bool
    embedding_provider: str
    model: str

class RootStatusResponse(BaseModel):
    """Root endpoint application information."""
    app: str = "Designs Law Assistant"
    version: str = "1.0.0"
    status: str = "operational"
    description: str = "Document-grounded RAG assistant for Manual of Designs Practice & Procedure (IP India)"
    docs_url: str = "/docs"
