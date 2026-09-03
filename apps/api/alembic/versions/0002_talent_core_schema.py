"""talent core schema: person, person_identity, profile_document, parse_run

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-03 16:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. person table
    op.create_table(
        "person",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("nationality", sa.String(length=100), nullable=True),
        sa.Column("primary_location", sa.String(length=255), nullable=True),
        sa.Column("visa_status", sa.String(length=100), nullable=True),
        sa.Column("notice_period_days", sa.Integer(), nullable=True),
        sa.Column("employment_state", sa.String(length=50), nullable=False, server_default="candidate"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_person_tenant_id", "person", ["tenant_id"])
    op.execute(
        "CREATE INDEX idx_person_full_name_trgm ON person USING gin (full_name gin_trgm_ops);"
    )

    # 2. person_identity table
    op.create_table(
        "person_identity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("person.id", ondelete="CASCADE"), nullable=False),
        sa.Column("identity_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_person_identity_tenant_id", "person_identity", ["tenant_id"])
    op.create_index("idx_person_identity_person_id", "person_identity", ["person_id"])
    op.create_index(
        "idx_person_identity_unique",
        "person_identity",
        ["tenant_id", "identity_type", "value"],
        unique=True,
    )

    # 3. profile_document table
    op.create_table(
        "profile_document",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("person.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("minio_bucket", sa.String(length=100), nullable=False, server_default="resumes"),
        sa.Column("minio_object_key", sa.String(length=500), nullable=False),
        sa.Column("file_hash_sha256", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("extraction_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_profile_document_tenant_id", "profile_document", ["tenant_id"])
    op.create_index("idx_profile_document_person_id", "profile_document", ["person_id"])
    op.create_index(
        "idx_doc_dedupe_tenant_hash",
        "profile_document",
        ["tenant_id", "file_hash_sha256"],
    )

    # 4. parse_run table
    op.create_table(
        "parse_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profile_document.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_alias", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("raw_output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_parse_run_tenant_id", "parse_run", ["tenant_id"])
    op.create_index("idx_parse_run_document_id", "parse_run", ["document_id"])


def downgrade() -> None:
    op.drop_table("parse_run")
    op.drop_table("profile_document")
    op.drop_table("person_identity")
    op.execute("DROP INDEX IF EXISTS idx_person_full_name_trgm;")
    op.drop_table("person")
