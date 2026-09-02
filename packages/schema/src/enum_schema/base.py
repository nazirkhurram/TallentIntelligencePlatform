"""Base schemas and shared models adhering to the platform data specification."""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExtractionSource(StrEnum):
    """Extraction provenance source ladder."""
    REGEX = "regex"
    GAZETTEER = "gazetteer"
    NER = "ner"
    LLM = "llm"
    OCR = "ocr"
    AGENCY = "agency"
    SELF_SERVICE = "self_service"
    RECRUITER = "recruiter"


class EmploymentState(StrEnum):
    """Person employment status."""
    CANDIDATE = "candidate"
    INTERNAL_BENCH = "internal_bench"
    DEPLOYED = "deployed"
    ALUMNI = "alumni"


class ProvenanceField(BaseModel):
    """Field-level provenance model matching profile_field data contract."""
    model_config = ConfigDict(from_attributes=True)

    person_id: UUID
    field_path: str = Field(description="Dotted path of field, e.g. contact.phone")
    value: Any
    source: ExtractionSource
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    parse_run_id: UUID | None = None
    verified_by: UUID | None = None
    verified_at: datetime | None = None


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    services: dict[str, str] = Field(default_factory=dict)

