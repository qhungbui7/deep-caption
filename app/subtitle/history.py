from collections import deque

from app.models import TranslationSegment


class SubtitleHistory:
    def __init__(self, max_items: int = 100) -> None:
        self._items: deque[TranslationSegment] = deque(maxlen=max_items)

    def add(self, segment: TranslationSegment) -> None:
        self._items.append(segment)

    def recent(self) -> list[TranslationSegment]:
        return list(self._items)
