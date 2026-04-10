from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StableText:
    text: str
    is_final: bool
    ready_for_translation: bool


class SubtitleStabilizer:
    def __init__(self, idle_commit_ms: int = 700) -> None:
        self.idle_commit_ms = idle_commit_ms
        self._last_partial = ""
        self._last_update_ms = 0

    def consume_partial(self, text: str, now_ms: int) -> StableText:
        normalized = text.strip()
        self._last_partial = normalized
        self._last_update_ms = now_ms
        if len(normalized) <= 4:
            return StableText(text="", is_final=False, ready_for_translation=False)

        has_punctuation = normalized.endswith((".", ",", "!", "?", ";", ":"))
        return StableText(
            text=normalized,
            is_final=False,
            ready_for_translation=has_punctuation,
        )

    def maybe_commit_idle(self, now_ms: int) -> StableText | None:
        if not self._last_partial:
            return None
        if now_ms - self._last_update_ms < self.idle_commit_ms:
            return None
        return StableText(text=self._last_partial, is_final=False, ready_for_translation=True)

    def consume_final(self, text: str) -> StableText:
        normalized = text.strip()
        self._last_partial = ""
        return StableText(text=normalized, is_final=True, ready_for_translation=bool(normalized))
