from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QWidget,
)
from typing import Optional


class EditScenarioDialog(QDialog):
    def __init__(self, config, scenario: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Cenário")
        self.config = config
        self.scenario = dict(scenario)

        layout = QVBoxLayout(self)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0,0,0,0)
        row_layout.addWidget(QLabel("Nome:"))
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.scenario.get('name',''))
        row_layout.addWidget(self.name_edit)
        layout.addWidget(row)

        layout.addWidget(QLabel("Itens do cenário:"))
        self.items_list = QListWidget()
        layout.addWidget(self.items_list)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        self.remove_item_btn = QPushButton("Remover item")
        btn_layout.addWidget(self.remove_item_btn)
        btn_layout.addStretch()
        self.save_btn = QPushButton("Salvar")
        self.cancel_btn = QPushButton("Cancelar")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addWidget(btn_row)

        self.remove_item_btn.clicked.connect(self._remove_item)
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

        self._refresh_items()

    def _refresh_items(self):
        self.items_list.clear()
        for it in self.scenario.get('items', []):
            name = it.get('name')
            args = it.get('argument_names') or []
            preview = ', '.join(f"{n}={it.get('arguments',{}).get(n,'')}" for n in args) if args else ''
            li = QListWidgetItem(f"{name} [{preview}]")
            li.setData(0, it)
            self.items_list.addItem(li)

    def _remove_item(self):
        it = self.items_list.currentItem()
        if not it:
            return
        obj = it.data(0)
        new = [x for x in self.scenario.get('items', []) if x is not obj]
        self.scenario['items'] = new
        self._refresh_items()

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            return
        self.scenario['name'] = name
        # persist
        self.config.add_or_update_scenario(self.scenario)
        self.accept()
