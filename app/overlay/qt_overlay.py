from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.config import OverlayConfig


class QtOverlay(QWidget):
    def __init__(self, config: OverlayConfig, show_source_text: bool = False) -> None:
        super().__init__()
        self._config = config
        self._show_source_text = show_source_text
        self._ttl_timer = QTimer(self)
        self._ttl_timer.setSingleShot(True)
        self._ttl_timer.timeout.connect(self._fade)
        self._state = OverlayState.HIDDEN
        self._build_ui()
        self._position_bottom_center()

    def _build_ui(self) -> None:
        flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self._source_label = QLabel("", self)
        self._source_label.setWordWrap(True)
        self._source_label.setStyleSheet("color: #A3A3A3; font-size: 15px;")

        self._translated_label = QLabel("", self)
        self._translated_label.setWordWrap(True)
        self._translated_label.setStyleSheet("color: white; font-size: 24px; font-weight: 600;")

        container = QWidget(self)
        container.setStyleSheet(
            "background-color: rgba(18, 18, 18, 217); border-radius: 12px; padding: 10px;"
        )

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        layout.addWidget(self._source_label)
        layout.addWidget(self._translated_label)
        self._source_label.setVisible(self._show_source_text)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(container)
        self.resize(760, 120)

    def _position_bottom_center(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        width = int(geometry.width() * self._config.width_ratio)
        self.resize(width, self.height())
        x = geometry.x() + (geometry.width() - self.width()) // 2
        y = geometry.y() + geometry.height() - self.height() - self._config.bottom_margin_px
        self.move(x, y)

    def set_show_source_text(self, value: bool) -> None:
        self._show_source_text = value
        self._source_label.setVisible(value)

    def show_partial(self, text: str, source: str = "") -> None:
        self._state = OverlayState.PARTIAL
        self._translated_label.setText(text)
        self._translated_label.setStyleSheet("color: #D9D9D9; font-size: 22px; font-weight: 500;")
        if self._show_source_text:
            self._source_label.setText(source or text)
        self.show()

    def show_final(self, translated: str, source: str = "", ttl_ms: int = 2500) -> None:
        self._state = OverlayState.FINAL
        self._translated_label.setText(translated)
        self._translated_label.setStyleSheet("color: white; font-size: 24px; font-weight: 600;")
        if self._show_source_text:
            self._source_label.setText(source)
        self.show()
        self._ttl_timer.start(ttl_ms)

    def _fade(self) -> None:
        self._state = OverlayState.FADING
        self.clear()

    def clear(self) -> None:  # noqa: A003
        self._state = OverlayState.HIDDEN
        self._source_label.clear()
        self._translated_label.clear()
        self.hide()


class OverlayState(str, Enum):
    HIDDEN = "hidden"
    PARTIAL = "partial"
    FINAL = "final"
    FADING = "fading"
