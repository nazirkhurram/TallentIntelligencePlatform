"""Talent Core SQLAlchemy Models (Story 1020).

Defines:
- Person: Unified candidate & consultant model (Data Decision #1)
- PersonIdentity: Multi-identity support (email, phone, linkedin, etc.)
- ProfileDocument: Raw resume file metadata with SHA-256 deduplication
- ParseRun: Append-only model parse runs with versioning (Data Decision #3)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enum_api.core.database import Base


class EmploymentState(StrEnum):
    """Person employment lifecycle status."""

    CANDIDATE = "candidate"
    INTERNAL_BENCH = "internal_bench"
    DEPLOYED = "deployed"
    ALUMNI = "alumni"


class IdentityType(StrEnum):
    """Types of identity records."""

    EMAIL = "email"
    PHONE = "phone"
    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    LINKEDIN = "linkedin"


class DocumentExtractionStatus(StrEnum):
    """Document extraction lifecycle."""

    PENDING = "pending"
    PARSED = "parsed"
    FAILED = "failed"


class Person(Base):
    """Unified person entity for candidates, consultants, and alumni."""

    __tablename__ = "person"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    primary_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    visa_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notice_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employment_state: Mapped[str] = mapped_column(
        String(50), nullable=False, default=EmploymentState.CANDIDATE.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    identities: Mapped[list[PersonIdentity]] = relationship(
        "PersonIdentity", back_populates="person", cascade="all, delete-orphan"
    )
    documents: Mapped[list[ProfileDocument]] = relationship(
        "ProfileDocument", back_populates="person", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "idx_person_full_name_trgm",
            "full_name",
            postgresql_using="gin",
            postgresql_ops={"full_name": "gin_trgm_ops"},
        ),
    )


class PersonIdentity(Base):
    """Identity record (email, phone, linkedin) linked to a person."""

    __tablename__ = "person_identity"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationship
    person: Mapped[Person] = relationship("Person", back_populates="identities")

    __table_args__ = (
        Index(
            "idx_person_identity_unique",
            "tenant_id",
            "identity_type",
            "value",
            unique=True,
        ),
    )


class ProfileDocument(Base):
    """Raw resume document metadata stored in MinIO."""

    __tablename__ = "profile_document"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    minio_bucket: Mapped[str] = mapped_column(String(100), default="resumes", nullable=False)
    minio_object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extraction_status: Mapped[str] = mapped_column(
        String(50), default=DocumentExtractionStatus.PENDING.value, nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationships
    person: Mapped[Person] = relationship("Person", back_populates="documents")
    parse_runs: Mapped[list[ParseRun]] = relationship(
        "ParseRun", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_doc_dedupe_tenant_hash", "tenant_id", "file_hash_sha256"),
    )


class ParseRun(Base):
    """Append-only parse execution record with model & prompt versioning."""

    __tablename__ = "parse_run"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profile_document.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_alias: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_output: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationship
    document: Mapped[ProfileDocument] = relationship("ProfileDocument", back_populates="parse_runs")
