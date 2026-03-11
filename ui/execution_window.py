from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QTextEdit,
    QPushButton,
)


class ExecutionWindow(QDialog):
    def __init__(self, suite_name: str, keywords: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tela de Execução")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Suite: {suite_name}"))

        layout.addWidget(QLabel("Keywords:"))
        self.kw_list = QListWidget()
        for k in keywords:
            self.kw_list.addItem(k)
        layout.addWidget(self.kw_list)

        layout.addWidget(QLabel("Logs:"))
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        layout.addWidget(self.logs)

        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)

    def append_log(self, text: str):
        self.logs.append(text)
