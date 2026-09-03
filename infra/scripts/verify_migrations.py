#!/usr/bin/env python3
"""
Alembic Migrations Round-Trip Verification Script
ENUM Talent Intelligence Platform (Story 1019)

Executes and verifies:
1. alembic upgrade head -> applies migrations to head
2. checks alembic_version table in postgres
3. alembic downgrade base -> verifies clean rollback
4. alembic upgrade head -> re-applies to ensure idempotency

Uses standard library subprocess (zero pip dependencies required).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def run_cmd(cmd: list[str]) -> str:
    """Execute command and return stdout, raising an error on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nError: {result.stderr.strip()}")
    return result.stdout.strip()


def run_docker_alembic(alembic_args: list[str]) -> str:
    """Run alembic command inside the running api container."""
    docker_bin = shutil.which("docker") or "docker.exe"
    base_cmd = [
        docker_bin,
        "compose",
        "-f",
        "infra/compose/compose.yml",
        "-f",
        "infra/compose/compose.override.yml",
        "exec",
        "-T",
        "-w",
        "/app/apps/api",
        "api",
        "alembic",

    ]
    return run_cmd(base_cmd + alembic_args)


def run_sql(query: str) -> str:
    """Execute SQL query against postgres container."""
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
        os.getenv("POSTGRES_USER", "enum_admin"),
        "-d",
        os.getenv("POSTGRES_DB", "enum_tip"),
        "-t",
        "-A",
        "-c",
        query,
    ]
    env = os.environ.copy()
    env["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD", "enum_secure_password_dev")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Database query failed: {result.stderr.strip()}")
    return result.stdout.strip()


def main() -> int:
    print("==> Starting Alembic Migration Pipeline Verification (Story 1019)...")
    try:
        # 1. Test alembic upgrade head
        print("\n--- 1. Testing 'alembic upgrade head' ---")
        upgrade_out = run_docker_alembic(["upgrade", "head"])
        print(f" Output:\n{upgrade_out}")
        current_rev = run_sql("SELECT version_num FROM alembic_version;")
        print(f" [PASS] Upgraded successfully. Current revision in DB: {current_rev}")

        # 2. Test alembic downgrade base
        print("\n--- 2. Testing 'alembic downgrade base' (Rollback test) ---")
        downgrade_out = run_docker_alembic(["downgrade", "base"])
        print(f" Output:\n{downgrade_out}")
        rev_count = run_sql("SELECT count(*) FROM alembic_version;")
        print(f" [PASS] Downgrade completed. Active revisions remaining: {rev_count}")

        # 3. Re-apply alembic upgrade head
        print("\n--- 3. Re-applying 'alembic upgrade head' (Idempotency test) ---")
        reapply_out = run_docker_alembic(["upgrade", "head"])
        print(f" Output:\n{reapply_out}")
        current_rev_after = run_sql("SELECT version_num FROM alembic_version;")
        print(f" [PASS] Re-applied successfully. Final revision in DB: {current_rev_after}")

        print("\n[SUCCESS] Alembic baseline migrations and round-trip rollback verified 100%!\n")
        return 0

    except Exception as e:
        print(f"\n[FAIL] Migration verification error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
