from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import Config
from app.core.supervisor import Supervisor
from app.overlay.hotkeys import HotkeyController
from app.overlay.qt_overlay import QtOverlay
from app.ui.logs_window import LogsWindow
from app.ui.source_picker import SourcePicker
from app.ui.tray import TrayController


class VoiceModeWindow(QMainWindow):
    def __init__(
        self,
        config: Config,
        config_path: Path,
        overlay: QtOverlay,
    ) -> None:
        super().__init__()
        self._config = config
        self._config_path = config_path
        self._overlay = overlay
        self._logs = LogsWindow()
        self._source_id = ""
        self._running = False
        self._supervisor: Supervisor | None = None

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_runtime)
        self._poll_timer.setInterval(120)

        self._status = QLabel("Idle", self)
        self._source_lbl = QLabel("Source: default", self)
        self._live_transcript_lbl = QLabel("Live transcript: (waiting)", self)
        self._live_transcript_lbl.setWordWrap(True)
        self._build_ui()
        self._install_hotkeys()
        self._tray = TrayController(
            parent=self,
            on_show=self.showNormal,
            on_toggle_voice=self._toggle_runtime,
            on_quit=self.close,
        )
        self._tray.start()

    def _build_ui(self) -> None:
        self.setWindowTitle("Deep Caption - Voice Mode")
        self.resize(720, 180)
        source_btn = QPushButton("Pick Source", self)
        source_btn.clicked.connect(self._pick_source)
        start_btn = QPushButton("Start/Stop Voice", self)
        start_btn.clicked.connect(self._toggle_runtime)
        logs_btn = QPushButton("Logs", self)
        logs_btn.clicked.connect(self._logs.show)

        row = QHBoxLayout()
        row.addWidget(source_btn)
        row.addWidget(start_btn)
        row.addWidget(logs_btn)
        row.addStretch(1)

        root = QVBoxLayout()
        root.addLayout(row)
        root.addWidget(self._source_lbl)
        root.addWidget(self._status)
        root.addWidget(self._live_transcript_lbl)
        wrapper = QWidget(self)
        wrapper.setLayout(root)
        self.setCentralWidget(wrapper)

    def _install_hotkeys(self) -> None:
        keys = HotkeyController(self)
        keys.register_defaults(
            toggle_overlay=self._toggle_overlay,
            toggle_source_text=self._toggle_source_text,
        )
        self._keys = keys

    def _pick_source(self) -> None:
        dlg = SourcePicker(self)
        if dlg.exec():
            self._source_id = dlg.selected_source_id()
            self._source_lbl.setText(f"Source: {self._source_id or 'default'}")

    def _toggle_runtime(self) -> None:
        if self._running:
            self._stop_runtime()
        else:
            self._start_runtime()

    def _start_runtime(self) -> None:
        self._supervisor = Supervisor(
            config=self._config,
            source_id=self._source_id,
            target_lang=self._config.app.target_language,
        )
        self._supervisor.start()
        self._running = True
        self._status.setText("Running")
        self._logs.append("Voice runtime started")
        self._poll_timer.start()

    def _stop_runtime(self) -> None:
        self._poll_timer.stop()
        if self._supervisor is not None:
            self._supervisor.stop()
            self._supervisor = None
        self._running = False
        self._status.setText("Stopped")
        self._logs.append("Voice runtime stopped")

    def _poll_runtime(self) -> None:
        if self._supervisor is None:
            return
        for segment in self._supervisor.poll():
            self._status.setText(f"{segment.source_lang}->{segment.target_lang}")
            self._live_transcript_lbl.setText(f"Live transcript: {segment.source_text}")
            if segment.is_final:
                translated = segment.translated_text or segment.source_text
                self._overlay.show_final(
                    translated=translated,
                    source=segment.source_text,
                    ttl_ms=2500,
                )
                self._logs.append(f"{segment.source_text} => {translated}")
            else:
                self._overlay.show_partial(segment.source_text, source=segment.source_text)

    def _toggle_overlay(self) -> None:
        if self._overlay.isVisible():
            self._overlay.hide()
        else:
            self._overlay.show()

    def _toggle_source_text(self) -> None:
        self._config.app.show_source_text = not self._config.app.show_source_text
        self._overlay.set_show_source_text(self._config.app.show_source_text)
        self._config.save(self._config_path)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._stop_runtime()
        super().closeEvent(event)
