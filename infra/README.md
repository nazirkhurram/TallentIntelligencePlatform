# Infrastructure Runbook & Database Architecture

This document details the container infrastructure, Docker Compose topologies, PostgreSQL 16 extensions and tuning, and the **Model Weights Volume Strategy** for the **ENUM Talent Intelligence Platform**.

---

## 1. PostgreSQL 16 Extensions & Performance Tuning (Story 1018)

PostgreSQL 16 serves as the single unified data store for relational models, dense vector embeddings, full-text search, and fuzzy matching.

### Required Extensions
* **`uuid-ossp`**: Native UUID generation for distributed primary keys.
* **`vector` (`pgvector`)**: Stores 384-dimensional dense embeddings with HNSW cosine indexes for cross-lingual semantic matching (English, Arabic, Urdu).
* **`pg_trgm`**: Trigram matching for fuzzy searching over candidate names, job titles, and skills.
* **`unaccent`**: Diacritics and accent normalization.

### Engine Memory Tuning (On-Premise Profile)
Memory settings are configured to balance RAM between PostgreSQL operations and CPU model inference:
* `shared_buffers = 256MB` (Development) / `1024MB` (Production)
* `work_mem = 16MB` (Development) / `32MB` (Production)
* `maintenance_work_mem = 64MB` (Development) / `256MB` (Production for fast HNSW index builds)
* `effective_cache_size = 1GB` (Development) / `3GB` (Production)

### Extension & Tuning Verification
To run automated smoke queries verifying all 4 extensions and active tuning values:
```powershell
python infra/scripts/verify_db_extensions.py
```

---

## 2. Model Weights Strategy (Story 1011)

### Architectural Guardrail: Zero Model Files in Image Layers
Machine learning weights (GGUF and ONNX models) are **never baked into Docker images**.
* Avoids multi-gigabyte container image sizes and long CI/CD build times.
* Mounted at runtime from `infra/model-weights/` into `/models:ro`.
* All models are verified via SHA-256 cryptographic checksums before loading.

### How to Fetch & Verify Models
```powershell
# Dry run check
python infra/scripts/fetch_models.py --dry-run

# Download and verify checksums
python infra/scripts/fetch_models.py
```

---

## 3. Ephemeral Self-Hosted Runner (Story 1013)

### Security Hardening Measures
* **Ephemeral Lifecycle (`--ephemeral`):** Runner executes exactly 1 job and automatically unregisters.
* **Repository Scoping:** Strictly registered to this private repository.

### Launching on the On-Premise VM
```bash
cd infra/runner
RUNNER_TOKEN="<YOUR_TOKEN>" docker compose -f compose.runner.yml up -d --build
```
