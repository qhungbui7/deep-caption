from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget


class HotkeyController:
    def __init__(self, parent: QWidget) -> None:
        self.parent = parent
        self._shortcuts: list[QShortcut] = []

    def register_defaults(
        self,
        toggle_overlay: Callable[[], None],
        toggle_source_text: Callable[[], None],
    ) -> None:
        self._bind("Ctrl+Shift+O", toggle_overlay)
        self._bind("Ctrl+Shift+S", toggle_source_text)

    def _bind(self, key: str, callback: Callable[[], None]) -> None:
        shortcut = QShortcut(QKeySequence(key), self.parent)
        shortcut.activated.connect(callback)
        self._shortcuts.append(shortcut)
