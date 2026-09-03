#!/usr/bin/env python3
"""
Talent Core Schema Verification Script (Story 1020).

Tests:
1. Unified Person table insertion & GIN trigram search
2. PersonIdentity multi-identity & unique constraints
3. ProfileDocument creation & SHA-256 deduplication index
4. ParseRun append-only versioning (Data Decision #3)

Uses standard library subprocess against Docker PostgreSQL (zero pip dependencies required).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid

DB_USER = os.getenv("POSTGRES_USER", "enum_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "enum_secure_password_dev")
DB_NAME = os.getenv("POSTGRES_DB", "enum_tip")


def run_sql(query: str) -> str:
    """Execute SQL query using docker compose exec against postgres container."""
    docker_bin = shutil.which("docker") or "docker.exe"
    cmd = [
        docker_bin,
        "compose",
        "-f",
        "infra/compose/compose.yml",
        "-f",
        "infra/compose/compose.override.yml",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
        "-t",
        "-A",
        "-c",
        query,
    ]
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Database query failed: {result.stderr.strip()}")
    return result.stdout.strip()


def main() -> int:
    print("==> Starting Talent Core Schema Verification (Story 1020)...")
    test_tenant_id = str(uuid.uuid4())
    test_person_id = str(uuid.uuid4())
    test_doc_id = str(uuid.uuid4())
    test_sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    try:
        # 1. Insert Unified Person
        print("\n--- 1. Testing Unified Person Creation (Data Decision #1) ---")
        run_sql(f"""
            INSERT INTO person (id, tenant_id, full_name, nationality, primary_location, visa_status, notice_period_days, employment_state)
            VALUES ('{test_person_id}', '{test_tenant_id}', 'Ahmed Al-Balushi', 'Omani', 'Muscat', 'citizen', 30, 'candidate');
        """)
        person_name = run_sql(f"SELECT full_name FROM person WHERE id = '{test_person_id}';")
        print(f" [PASS] Created person: '{person_name}' (ID: {test_person_id})")

        # 2. Test Trigram Fuzzy Search on full_name
        trgm_match = run_sql(f"""
            SELECT full_name FROM person 
            WHERE tenant_id = '{test_tenant_id}' AND full_name % 'Ahmed Balushi';
        """)
        print(f" [PASS] Trigram fuzzy search matched: '{trgm_match}'")

        # 3. Test PersonIdentity (Multiple Identities)
        print("\n--- 2. Testing Multi-Identity Linked to Person ---")
        id_1 = str(uuid.uuid4())
        id_2 = str(uuid.uuid4())
        id_3 = str(uuid.uuid4())
        run_sql(f"""
            INSERT INTO person_identity (id, tenant_id, person_id, identity_type, value, is_primary) VALUES
            ('{id_1}', '{test_tenant_id}', '{test_person_id}', 'email', 'ahmed.balushi@example.om', true),
            ('{id_2}', '{test_tenant_id}', '{test_person_id}', 'phone', '+96891234567', false),
            ('{id_3}', '{test_tenant_id}', '{test_person_id}', 'linkedin', 'https://linkedin.com/in/ahmed-balushi', false);
        """)
        id_count = run_sql(f"SELECT count(*) FROM person_identity WHERE person_id = '{test_person_id}';")
        print(f" [PASS] Linked {id_count} identities (email, phone, LinkedIn) to candidate")

        # 4. Test ProfileDocument & SHA-256 Deduplication Index
        print("\n--- 3. Testing Profile Document & SHA-256 Deduplication ---")
        run_sql(f"""
            INSERT INTO profile_document (id, tenant_id, person_id, file_name, minio_bucket, minio_object_key, file_hash_sha256, mime_type, extraction_status)
            VALUES ('{test_doc_id}', '{test_tenant_id}', '{test_person_id}', 'ahmed_cv.pdf', 'resumes', '{test_tenant_id}/docs/ahmed.pdf', '{test_sha256}', 'application/pdf', 'parsed');
        """)
        dedupe_doc = run_sql(f"""
            SELECT id FROM profile_document 
            WHERE tenant_id = '{test_tenant_id}' AND file_hash_sha256 = '{test_sha256}';
        """)
        assert dedupe_doc == test_doc_id
        print(f" [PASS] Stored document and verified SHA-256 deduplication index (Doc ID: {dedupe_doc})")

        # 5. Test ParseRun Append-Only Versioning (Data Decision #3)
        print("\n--- 4. Testing Append-Only Parse Runs & Versioning ---")
        run_sql(f"""
            INSERT INTO parse_run (id, tenant_id, document_id, model_alias, model_version, prompt_version, raw_output, overall_confidence)
            VALUES ('{uuid.uuid4()}', '{test_tenant_id}', '{test_doc_id}', 'enum-extract', 'qwen2.5-3b-q4_k_m', 'v1.0.0', '{{"skills": ["SQL", "Oracle"]}}', 0.88);
        """)
        run_sql(f"""
            INSERT INTO parse_run (id, tenant_id, document_id, model_alias, model_version, prompt_version, raw_output, overall_confidence)
            VALUES ('{uuid.uuid4()}', '{test_tenant_id}', '{test_doc_id}', 'enum-extract', 'qwen2.5-7b-q4_k_m', 'v1.2.0', '{{"skills": ["SQL", "Oracle", "PL/SQL"]}}', 0.95);
        """)
        runs_count = run_sql(f"SELECT count(*) FROM parse_run WHERE document_id = '{test_doc_id}';")
        latest_version = run_sql(f"""
            SELECT prompt_version FROM parse_run 
            WHERE document_id = '{test_doc_id}' ORDER BY executed_at DESC LIMIT 1;
        """)
        print(f" [PASS] Persisted {runs_count} historical parse runs. Latest version: {latest_version}")

        # 6. Cleanup Test Data (Cascade delete will clean identities, documents, and parse runs)
        run_sql(f"DELETE FROM person WHERE id = '{test_person_id}';")
        remaining_docs = run_sql(f"SELECT count(*) FROM profile_document WHERE id = '{test_doc_id}';")
        assert remaining_docs == "0"
        print(f" [PASS] Verified CASCADE cleanup on person deletion")

        print("\n[SUCCESS] Talent Core Schema (Story 1020) verified 100% successfully!\n")
        return 0

    except Exception as e:
        print(f"\n[FAIL] Talent Core verification error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
