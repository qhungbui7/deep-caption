from app.config import OverlayConfig
from app.overlay.qt_overlay import QtOverlay


class X11Overlay(QtOverlay):
    def __init__(self, config: OverlayConfig, show_source_text: bool = False) -> None:
        super().__init__(config=config, show_source_text=show_source_text)
        self._experimental = False
