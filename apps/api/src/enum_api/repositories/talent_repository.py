"""Async Talent Core Repository Layer (Story 1020)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from enum_api.models.talent_core import (
    ParseRun,
    Person,
    PersonIdentity,
    ProfileDocument,
)


class TalentRepository:
    """Data access repository for unified Person, Identity, Document, and ParseRun entities."""

    @staticmethod
    async def create_person(
        session: AsyncSession,
        person: Person,
        identities: list[PersonIdentity] | None = None,
    ) -> Person:
        """Create a new unified person record with optional initial identities."""
        session.add(person)
        await session.flush()

        if identities:
            for identity in identities:
                identity.person_id = person.id
                identity.tenant_id = person.tenant_id
                session.add(identity)
            await session.flush()

        await session.commit()
        await session.refresh(person)
        return person

    @staticmethod
    async def get_person_by_id(
        session: AsyncSession,
        person_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> Person | None:
        """Retrieve person by ID with preloaded identities and documents."""
        stmt = (
            select(Person)
            .options(selectinload(Person.identities), selectinload(Person.documents))
            .where(Person.id == person_id, Person.tenant_id == tenant_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def find_person_by_identity(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        identity_type: str,
        value: str,
    ) -> Person | None:
        """Find person by normalized identity value (email, phone, linkedin)."""
        stmt = (
            select(Person)
            .join(PersonIdentity, Person.id == PersonIdentity.person_id)
            .options(selectinload(Person.identities))
            .where(
                PersonIdentity.tenant_id == tenant_id,
                PersonIdentity.identity_type == identity_type,
                PersonIdentity.value == value,
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_document(
        session: AsyncSession,
        document: ProfileDocument,
    ) -> ProfileDocument:
        """Store resume document metadata."""
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document

    @staticmethod
    async def find_document_by_hash(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        file_hash_sha256: str,
    ) -> ProfileDocument | None:
        """Find existing document by SHA-256 hash for content deduplication."""
        stmt = select(ProfileDocument).where(
            ProfileDocument.tenant_id == tenant_id,
            ProfileDocument.file_hash_sha256 == file_hash_sha256,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_parse_run(
        session: AsyncSession,
        parse_run: ParseRun,
    ) -> ParseRun:
        """Append a new versioned parse run record."""
        session.add(parse_run)
        await session.commit()
        await session.refresh(parse_run)
        return parse_run

    @staticmethod
    async def get_parse_runs_for_document(
        session: AsyncSession,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> list[ParseRun]:
        """Fetch all historical parse runs for a document, ordered chronologically."""
        stmt = (
            select(ParseRun)
            .where(ParseRun.document_id == document_id, ParseRun.tenant_id == tenant_id)
            .order_by(ParseRun.executed_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
