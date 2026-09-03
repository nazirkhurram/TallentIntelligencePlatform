"""Integration tests for Talent Core schema and repository (Story 1020)."""

from __future__ import annotations

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from enum_api.core.database import async_session_factory
from enum_api.models.talent_core import (
    EmploymentState,
    IdentityType,
    ParseRun,
    Person,
    PersonIdentity,
    ProfileDocument,
)
from enum_api.repositories.talent_repository import TalentRepository


@pytest.fixture
async def db_session() -> AsyncSession:
    """Provide clean database session for test execution."""
    async with async_session_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_create_person_with_multiple_identities(db_session: AsyncSession) -> None:
    """Verify a person can hold multiple identities (Story 1020)."""
    tenant_id = uuid.uuid4()
    person = Person(
        tenant_id=tenant_id,
        full_name="Ahmed Al-Balushi",
        nationality="Omani",
        primary_location="Muscat",
        visa_status="citizen",
        notice_period_days=30,
        employment_state=EmploymentState.CANDIDATE.value,
    )
    identities = [
        PersonIdentity(
            identity_type=IdentityType.EMAIL.value,
            value="ahmed.balushi@example.om",
            is_primary=True,
        ),
        PersonIdentity(
            identity_type=IdentityType.PHONE.value,
            value="+96891234567",
            is_primary=False,
        ),
        PersonIdentity(
            identity_type=IdentityType.LINKEDIN.value,
            value="https://linkedin.com/in/ahmed-balushi",
            is_primary=False,
        ),
    ]

    saved_person = await TalentRepository.create_person(db_session, person, identities)
    assert saved_person.id is not None
    assert len(saved_person.identities) == 3

    # Retrieve and verify
    fetched = await TalentRepository.get_person_by_id(db_session, saved_person.id, tenant_id)
    assert fetched is not None
    assert fetched.full_name == "Ahmed Al-Balushi"
    assert len(fetched.identities) == 3


@pytest.mark.asyncio
async def test_find_person_by_identity(db_session: AsyncSession) -> None:
    """Verify identity lookup resolves to the correct candidate."""
    tenant_id = uuid.uuid4()
    person = Person(
        tenant_id=tenant_id,
        full_name="Tariq Khan",
        nationality="Pakistani",
        primary_location="Karachi",
    )
    identities = [
        PersonIdentity(
            identity_type=IdentityType.EMAIL.value,
            value="tariq.khan@example.pk",
            is_primary=True,
        )
    ]
    await TalentRepository.create_person(db_session, person, identities)

    found = await TalentRepository.find_person_by_identity(
        db_session, tenant_id, IdentityType.EMAIL.value, "tariq.khan@example.pk"
    )
    assert found is not None
    assert found.full_name == "Tariq Khan"


@pytest.mark.asyncio
async def test_document_and_parse_run_versioning(db_session: AsyncSession) -> None:
    """Verify multiple documents and append-only versioned parse runs (Data Decision #3)."""
    tenant_id = uuid.uuid4()
    person = Person(
        tenant_id=tenant_id,
        full_name="Priya Sharma",
        nationality="Indian",
        primary_location="Mumbai",
    )
    saved_person = await TalentRepository.create_person(db_session, person)

    # 1. Add Document with SHA-256 Hash
    sha256_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    doc = ProfileDocument(
        tenant_id=tenant_id,
        person_id=saved_person.id,
        file_name="priya_sharma_cv_2026.pdf",
        minio_bucket="resumes",
        minio_object_key=f"{tenant_id}/docs/{uuid.uuid4()}.pdf",
        file_hash_sha256=sha256_hash,
        mime_type="application/pdf",
    )
    saved_doc = await TalentRepository.create_document(db_session, doc)
    assert saved_doc.id is not None

    # Deduplication check
    existing_doc = await TalentRepository.find_document_by_hash(db_session, tenant_id, sha256_hash)
    assert existing_doc is not None
    assert existing_doc.id == saved_doc.id

    # 2. Append Versioned Parse Runs
    run_1 = ParseRun(
        tenant_id=tenant_id,
        document_id=saved_doc.id,
        model_alias="enum-extract",
        model_version="qwen2.5-3b-q4_k_m",
        prompt_version="v1.0.0",
        raw_output={"skills": ["Python", "SQL"], "years_experience": 5},
        overall_confidence=0.88,
    )
    await TalentRepository.create_parse_run(db_session, run_1)

    # Model upgrade to v1.2.0 (appends new row without overwriting prior run)
    run_2 = ParseRun(
        tenant_id=tenant_id,
        document_id=saved_doc.id,
        model_alias="enum-extract",
        model_version="qwen2.5-7b-q4_k_m",
        prompt_version="v1.2.0",
        raw_output={"skills": ["Python", "SQL", "PostgreSQL", "FastAPI"], "years_experience": 6},
        overall_confidence=0.96,
    )
    await TalentRepository.create_parse_run(db_session, run_2)

    runs = await TalentRepository.get_parse_runs_for_document(db_session, saved_doc.id, tenant_id)
    assert len(runs) == 2
    assert runs[0].prompt_version == "v1.0.0"
    assert runs[1].prompt_version == "v1.2.0"
    assert runs[1].overall_confidence == 0.96
