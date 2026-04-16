from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)
from PySide6.QtCore import Qt
from typing import List, Dict, Optional


class KeywordArgumentsDialog(QDialog):
    """Simple dialog to collect values for keyword arguments.

    Use via: res = KeywordArgumentsDialog.get_arguments(parent, name, arg_names)
    Returns dict of name->value or None if cancelled.
    """

    def __init__(self, keyword_name: str, arg_names: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Keyword: {keyword_name}")
        self.arg_names = list(arg_names)
        self._edits: Dict[str, QLineEdit] = {}

        layout = QVBoxLayout(self)

        for arg in self.arg_names:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(f"{arg}:")
            lbl.setFixedWidth(120)
            edit = QLineEdit()
            edit.setPlaceholderText(arg)
            row_layout.addWidget(lbl)
            row_layout.addWidget(edit, 1)
            layout.addWidget(row)
            self._edits[arg] = edit

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()
        self.confirm_btn = QPushButton("Confirmar")
        self.cancel_btn = QPushButton("Cancelar")
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addWidget(btn_row)

        self.confirm_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_values(self) -> Dict[str, str]:
        return {n: self._edits[n].text() for n in self.arg_names}

    @staticmethod
    def get_arguments(parent, keyword_name: str, arg_names: List[str]) -> Optional[Dict[str, str]]:
        d = KeywordArgumentsDialog(keyword_name, arg_names, parent=parent)
        ok = d.exec()
        if ok:
            return d.get_values()
        return None
