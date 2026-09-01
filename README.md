# ENUM Talent Intelligence Platform

An AI-native talent platform unifying external candidate intake, internal consultant bench management, and client requisition pipelines on self-hosted infrastructure.

## Monorepo Layout
- `apps/api`: FastAPI backend modular monolith
- `apps/worker`: Celery asynchronous processing workers
- `apps/web`: Next.js 15 frontend application
- `packages/schema`: Shared data models and DTO contracts
- `infra`: Docker Compose and deployment configurations
- `docs`: Architecture Decision Records (ADRs) and compliance docs
- `evals`: Benchmarks and golden dataset evaluation harness
