"""Shared Faker instance and common helper factories for seed data.

Seed functions (added once the underlying database models exist)
should import from here instead of creating their own Faker
instance, so that fake data stays consistent and unique across
the whole seed run.
"""

from faker import Faker

fake = Faker()


def fake_full_name() -> str:
    """Generate a random full name."""
    return fake.name()


def fake_email(unique: bool = True) -> str:
    """Generate a random email address.

    Set unique=True (default) to avoid duplicate emails when
    seeding many records in the same run.
    """
    return fake.unique.email() if unique else fake.email()


def fake_job_title() -> str:
    """Generate a random job title."""
    return fake.job()


def fake_company_name() -> str:
    """Generate a random company name."""
    return fake.company()


def fake_phone_number() -> str:
    """Generate a random phone number."""
    return fake.phone_number()


def fake_past_date_range() -> tuple[str, str]:
    """Generate a plausible (start_date, end_date) pair for work history
    or education entries, as ISO-format date strings.
    """
    start = fake.date_between(start_date="-10y", end_date="-2y")
    end = fake.date_between(start_date=start, end_date="today")
    return start.isoformat(), end.isoformat()