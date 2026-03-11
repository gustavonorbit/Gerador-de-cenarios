"""
Console panel to show execution logs and messages.

Responsibility:
 - Provide a simple read-only text area where execution output and parsed results will be shown.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit


class ConsolePanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

    def append_text(self, content: str):
        self.text.append(content)
