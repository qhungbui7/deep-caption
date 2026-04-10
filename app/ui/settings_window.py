from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from app.config import Config


class SettingsWindow(QDialog):
    settings_updated = Signal(str, bool)

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Deep Caption Settings")
        self.setModal(True)
        self._config = config
        self._target_lang = QLineEdit(self._config.app.target_language, self)
        self._show_source = QCheckBox("Show source text", self)
        self._show_source.setChecked(self._config.app.show_source_text)
        self._build_ui()

    def _build_ui(self) -> None:
        form = QFormLayout()
        form.addRow("Target language (ISO code)", self._target_lang)
        form.addRow("", self._show_source)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(buttons)

    def _save(self) -> None:
        target = self._target_lang.text().strip().lower() or self._config.app.target_language
        show_source = self._show_source.isChecked()
        self.settings_updated.emit(target, show_source)
        self.accept()
