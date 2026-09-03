#!/usr/bin/env python3
"""
PostgreSQL 16 Extensions & Tuning Verification Script
ENUM Talent Intelligence Platform (Story 1018)

Executes smoke queries exercising:
1. uuid-ossp (UUID v4 generation)
2. pgvector (Vector distance operations)
3. pg_trgm (Trigram fuzzy string similarity)
4. unaccent (Multilingual accent stripping)
And checks engine memory tuning parameters.
Uses standard library subprocess with docker compose exec (zero pip dependencies required).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

DB_USER = os.getenv("POSTGRES_USER", "enum_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "enum_secure_password_dev")
DB_NAME = os.getenv("POSTGRES_DB", "enum_tip")


def run_sql(query: str) -> str:
    """Execute SQL query using docker compose exec against the running postgres container."""
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
    print(f"==> Verifying PostgreSQL 16 extensions & tuning on database '{DB_NAME}'...")
    try:
        print("\n--- 1. Verifying Extensions & Smoke Queries ---")

        # 1. uuid-ossp smoke query
        uuid_val = run_sql("SELECT uuid_generate_v4()::text;")
        print(f" [PASS] uuid-ossp: generated UUID -> {uuid_val}")

        # 2. pgvector smoke query
        vec_dist = run_sql(
            "SELECT ('[0.1, 0.2, 0.3]'::vector(3) <=> '[0.1, 0.2, 0.4]'::vector(3))::text;"
        )
        print(f" [PASS] pgvector: computed cosine distance -> {float(vec_dist):.4f}")

        # 3. pg_trgm smoke query
        sim_val = run_sql("SELECT similarity('Bank of Oman', 'Bank Oman')::text;")
        print(f" [PASS] pg_trgm: computed trigram similarity -> {float(sim_val):.4f}")

        # 4. unaccent smoke query
        unacc_val = run_sql("SELECT unaccent('Café résumé élite');")
        print(f" [PASS] unaccent: normalized text -> '{unacc_val}'")

        print("\n--- 2. Verifying Engine Memory Tuning ---")
        settings = [
            "shared_buffers",
            "work_mem",
            "maintenance_work_mem",
            "effective_cache_size",
        ]
        for setting in settings:
            val = run_sql(f"SHOW {setting};")
            print(f"  * {setting} = {val}")

        print("\n[SUCCESS] All PostgreSQL 16 extensions and tuning verified successfully!\n")
        return 0

    except Exception as e:
        print(f"\n[FAIL] Extension smoke verification failed: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
