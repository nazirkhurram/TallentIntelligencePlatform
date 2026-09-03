"""Runner that discovers and executes all registered seed functions.

Run this module directly to seed the database with development
fixture data:

    uv run python -m enum_api.seeds.runner
"""

import asyncio
import logging

from enum_api.seeds.registry import get_registered_seeds

logger = logging.getLogger("enum_api.seeds")


async def run_all_seeds() -> None:
    """Execute every registered seed function, in registration order."""
    seeds = get_registered_seeds()

    if not seeds:
        logger.warning(
            "No seed functions are registered yet. "
            "Add seed functions under enum_api/seeds/ once the "
            "underlying database models exist."
        )
        return

    logger.info("Running %d registered seed(s): %s", len(seeds), ", ".join(seeds))

    for name, seed_func in seeds.items():
        logger.info("Seeding: %s ...", name)
        await seed_func()
        logger.info("Done: %s", name)

    logger.info("All seeds completed successfully.")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run_all_seeds())


if __name__ == "__main__":
    main()