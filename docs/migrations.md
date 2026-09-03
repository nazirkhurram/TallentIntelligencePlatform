# Database Migration Policy & Conventions

This document outlines the database migration architecture, file naming conventions, review rules, and rollback testing for the **ENUM Talent Intelligence Platform**.

---

## 1. Architecture

* **Engine:** Alembic with asynchronous SQLAlchemy (`asyncpg`).
* **Location:** Configuration lives at `apps/api/alembic.ini` with migration scripts in `apps/api/alembic/versions/`.
* **Database Driver:** `postgresql+asyncpg` for non-blocking I/O.

---

## 2. Naming Conventions

Migration filenames must follow a 4-digit sequential prefix followed by a concise snake_case slug:

```text
XXXX_<action>_<entity>.py
```

### Examples:
* `0001_baseline_schema.py`
* `0002_talent_core_tables.py`
* `0003_field_provenance_schema.py`
* `0004_skills_taxonomy.py`

---

## 3. Migration Review Checklist & Governance Rules

Before any database migration PR is approved:

1. **Tested Forward & Backward Execution:**
   * `alembic upgrade head` must run cleanly.
   * `alembic downgrade -1` (or `downgrade base`) must cleanly rollback all created structures without leftover locks or orphaned constraints.
2. **Zero-Downtime Safe Patterns (Expand-and-Contract):**
   * **Adding Columns:** Add new columns as `nullable=True` (or with safe defaults) so old running application containers continue functioning without error.
   * **Renaming/Removing Columns:** Never drop or rename columns in a single deployment. Mark as deprecated, deploy new code, then drop in a subsequent release.
3. **Index Creation:**
   * Create large indexes with `postgresql_concurrently=True` where applicable to avoid table read/write locks.
4. **Row-Level Security (RLS) Compliance:**
   * All multi-tenant tables must have RLS enabled in the migration (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`).

---

## 4. Running Migrations

### Inside Docker Container / CI:
```bash
# Upgrade to latest migration
docker compose exec api alembic -c apps/api/alembic.ini upgrade head

# Rollback one migration
docker compose exec api alembic -c apps/api/alembic.ini downgrade -1

# Check current revision status
docker compose exec api alembic -c apps/api/alembic.ini current
```


### Automated Verification Script:
```powershell
python infra/scripts/verify_migrations.py
```
