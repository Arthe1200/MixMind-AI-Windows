"""Provider interface shared by local and remote AI backends."""

from __future__ import annotations

from typing import Protocol


class AIProvider(Protocol):
    """Minimal contract for a text-based planning assistant."""

    @property
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    def suggest_transition(self, prompt: str) -> str:
        """Return a suggestion; never execute audio operations directly."""
        ...
