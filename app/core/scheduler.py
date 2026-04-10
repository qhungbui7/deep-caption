from dataclasses import dataclass


@dataclass(slots=True)
class Scheduler:
    """Placeholder for cross-process scheduling policies."""

    tick_ms: int = 50
