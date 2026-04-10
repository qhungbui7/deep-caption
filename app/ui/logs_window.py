from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget


class LogsWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Deep Caption Logs")
        self.resize(680, 320)
        self._box = QPlainTextEdit(self)
        self._box.setReadOnly(True)
        root = QVBoxLayout(self)
        root.addWidget(self._box)

    def append(self, message: str) -> None:
        self._box.appendPlainText(message)
