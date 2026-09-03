# Seed & Fixture Framework

This package provides a lightweight framework for populating the
database with development and test data. It uses a **registry
pattern**: individual seed functions register themselves, and the
runner discovers and executes all of them.

## How it works

- `registry.py` — provides the `@register_seed` decorator and the
  `get_registered_seeds()` lookup used by the runner.
- `factories.py` — a shared `Faker` instance plus common helper
  functions (fake names, emails, job titles, etc.) so fake data
  stays consistent and unique across a seed run.
- `runner.py` — discovers all registered seeds and runs them, in the
  order they were registered.

## Adding a new seed function

Once the underlying SQLAlchemy model exists, add a new file in this
folder (e.g. `persons.py`) and register a seed function:

```python
from enum_api.seeds.registry import register_seed
from enum_api.seeds.factories import fake_full_name, fake_email

# from enum_api.models.person import Person  # once this model exists
# from enum_api.db import get_session          # once a session util exists


@register_seed("persons")
async def seed_persons(count: int = 20) -> None:
    """Insert `count` fake person records for local development."""
    async with get_session() as session:
        for _ in range(count):
            person = Person(
                full_name=fake_full_name(),
                email=fake_email(),
            )
            session.add(person)
        await session.commit()
```

Then import the new module once, e.g. in `runner.py` or a small
`__init__.py` import block, so the decorator runs and the seed gets
registered before `run_all_seeds()` is called.

## Running the seeds

Inside the API container:

```bash
docker compose -f infra/compose/compose.yml exec api uv run --no-sync python -m enum_api.seeds.runner
```

If no seed functions are registered yet, the runner logs a warning
and exits cleanly — this is expected until the first models and
their seed functions are added.

## Conventions

- One seed module per entity (e.g. `persons.py`, `skills.py`).
- Seed function names should be descriptive and registered under a
  short, unique name (e.g. `"persons"`, `"skills"`).
- Seed functions should be **idempotent-friendly** where practical —
  prefer checking for existing data or using a fixed random seed if
  a seed function may be run more than once in the same environment.
- Keep fake data generation in `factories.py` so it can be reused
  across multiple seed modules.