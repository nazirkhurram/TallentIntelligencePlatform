"""Registry for seed functions used by the seed and fixture framework.

Each seed function registers itself here using the @register_seed
decorator. The runner then discovers and executes all registered
seeds in the order they were registered.
"""

from collections.abc import Awaitable, Callable

# A seed function takes no arguments and returns nothing (it inserts
# data into the database as a side effect).
SeedFunc = Callable[[], Awaitable[None]]

_registry: dict[str, SeedFunc] = {}


def register_seed(name: str) -> Callable[[SeedFunc], SeedFunc]:
    """Decorator that registers a seed function under a given name.

    Usage:
        @register_seed("persons")
        async def seed_persons() -> None:
            ...
    """

    def decorator(func: SeedFunc) -> SeedFunc:
        if name in _registry:
            raise ValueError(f"A seed named '{name}' is already registered.")
        _registry[name] = func
        return func

    return decorator


def get_registered_seeds() -> dict[str, SeedFunc]:
    """Return a copy of all currently registered seed functions."""
    return dict(_registry)