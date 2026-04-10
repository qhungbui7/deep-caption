from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QStyle, QSystemTrayIcon, QWidget


class TrayController:
    def __init__(
        self,
        parent: QWidget,
        on_show: Callable[[], None],
        on_toggle_voice: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._tray = QSystemTrayIcon(parent)
        icon = parent.style().standardIcon(QStyle.SP_MediaPlay)
        self._tray.setIcon(icon)
        menu = QMenu(parent)
        show_action = QAction("Show Window", parent)
        show_action.triggered.connect(on_show)
        voice_action = QAction("Start/Stop Voice", parent)
        voice_action.triggered.connect(on_toggle_voice)
        quit_action = QAction("Quit", parent)
        quit_action.triggered.connect(on_quit)
        menu.addAction(show_action)
        menu.addAction(voice_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)

    def start(self) -> None:
        self._tray.show()
