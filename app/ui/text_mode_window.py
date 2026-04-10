from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import Config
from app.core.pipeline import TextTranslationPipeline
from app.overlay.qt_overlay import QtOverlay
from app.ui.settings_window import SettingsWindow


class TextModeWindow(QMainWindow):
    def __init__(
        self,
        config: Config,
        config_path: Path,
        pipeline: TextTranslationPipeline,
        overlay: QtOverlay,
    ) -> None:
        super().__init__()
        self._config = config
        self._config_path = config_path
        self._pipeline = pipeline
        self._overlay = overlay
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._run_translation)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Deep Caption - Text Mode")
        self.resize(720, 180)

        self._input = QLineEdit(self)
        self._input.setPlaceholderText("Type source text...")
        self._input.textChanged.connect(self._on_text_changed)

        self._status = QLabel("Ready", self)
        self._translated = QLabel("", self)
        self._translated.setWordWrap(True)

        settings_btn = QPushButton("Settings", self)
        settings_btn.clicked.connect(self._open_settings)

        controls = QHBoxLayout()
        controls.addWidget(settings_btn)
        controls.addStretch(1)

        root = QVBoxLayout()
        root.addWidget(self._input)
        root.addLayout(controls)
        root.addWidget(self._status)
        root.addWidget(self._translated)

        wrapper = QWidget(self)
        wrapper.setLayout(root)
        self.setCentralWidget(wrapper)

    def _on_text_changed(self, text: str) -> None:
        if len(text.strip()) < 2:
            self._status.setText("Waiting for more text...")
            self._translated.setText("")
            self._overlay.clear()
            return
        self._status.setText("Typing...")
        self._debounce_timer.start(250)

    def _run_translation(self) -> None:
        segment = self._pipeline.translate_text(
            text=self._input.text(),
            target_lang=self._config.app.target_language,
        )
        if segment is None:
            return
        self._status.setText(f"{segment.source_lang} -> {segment.target_lang}")
        self._translated.setText(segment.translated_text)
        self._overlay.show_final(
            translated=segment.translated_text,
            source=segment.source_text,
            ttl_ms=2500,
        )

    def _open_settings(self) -> None:
        dialog = SettingsWindow(self._config, self)
        dialog.settings_updated.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self, target_language: str, show_source_text: bool) -> None:
        self._config.app.target_language = target_language
        self._config.app.show_source_text = show_source_text
        self._overlay.set_show_source_text(show_source_text)
        self._config.save(self._config_path)
