from __future__ import annotations

import sys

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QListWidget, QVBoxLayout

from app.capture.linux.source_discovery import list_sources


class SourcePicker(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Audio Source Picker")
        self.resize(520, 320)
        self._list = QListWidget(self)
        self._selected = ""
        sources = [("system", "System Default")]
        if sys.platform == "darwin":
            sources.append(("mac:system", "macOS System Audio (ScreenCaptureKit)"))
        else:
            for source in list_sources():
                sources.append((source.id, source.name))
        for source_id, source_name in sources:
            self._list.addItem(f"{source_id} :: {source_name}")
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root = QVBoxLayout(self)
        root.addWidget(self._list)
        root.addWidget(buttons)

    def selected_source_id(self) -> str:
        return self._selected

    def _save(self) -> None:
        item = self._list.currentItem()
        if item is not None:
            self._selected = item.text().split(" :: ", 1)[0]
        self.accept()
