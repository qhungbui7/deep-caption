import argparse
from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication

from app.config import Config
from app.core.pipeline import TextTranslationPipeline
from app.overlay.qt_overlay import QtOverlay
from app.overlay.wayland_overlay import WaylandOverlay
from app.overlay.x11_overlay import X11Overlay
from app.platform.linux_env import choose_overlay_backend
from app.ui.voice_window import VoiceModeWindow
from app.translation.router import TranslationRouter
from app.ui.text_mode_window import TextModeWindow


def main() -> int:
    args = _parse_args()
    app = QApplication([])
    config_path = Path(args.config)
    config = Config.load(config_path)

    router = TranslationRouter.build_default(config.translation)
    pipeline = TextTranslationPipeline(router=router)
    overlay = _build_overlay(config)
    if config.app.overlay_enabled:
        overlay.show()
        overlay.clear()

    if config.app.mode == "voice":
        window = VoiceModeWindow(
            config=config,
            config_path=config_path,
            overlay=overlay,
        )
    else:
        window = TextModeWindow(
            config=config,
            config_path=config_path,
            pipeline=pipeline,
            overlay=overlay,
        )
    window.show()
    return app.exec()


def _build_overlay(config: Config) -> QtOverlay:
    if sys.platform != "linux":
        return QtOverlay(config=config.overlay, show_source_text=config.app.show_source_text)
    backend = choose_overlay_backend(config.platform.linux_overlay_backend)
    if backend == "wayland":
        return WaylandOverlay(config=config.overlay, show_source_text=config.app.show_source_text)
    return X11Overlay(config=config.overlay, show_source_text=config.app.show_source_text)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deep Caption desktop app")
    parser.add_argument(
        "--config",
        default=str(Path.home() / ".config" / "deep-caption" / "config.yaml"),
        help="Path to runtime YAML config",
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
