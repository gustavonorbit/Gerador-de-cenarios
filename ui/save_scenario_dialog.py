from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)
from typing import Optional


class SaveScenarioDialog(QDialog):
    def __init__(self, parent=None, default_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Salvar Cenário")
        self._name_edit = QLineEdit()
        self._name_edit.setText(default_name)

        layout = QVBoxLayout(self)
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(QLabel("Nome do cenário:"))
        row_layout.addWidget(self._name_edit)
        layout.addWidget(row)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.addStretch()
        self.save_btn = QPushButton("Salvar")
        self.cancel_btn = QPushButton("Cancelar")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addWidget(btn_row)

        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

    def _on_save(self):
        name = self._name_edit.text().strip()
        if not name:
            return
        self.accept()

    def get_name(self) -> Optional[str]:
        txt = self._name_edit.text().strip()
        return txt if txt else None
