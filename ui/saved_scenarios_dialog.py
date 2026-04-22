from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QWidget,
)
from typing import Callable


class SavedScenariosDialog(QDialog):
    def __init__(self, config, on_load: Callable[[dict], None], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cenários Salvos")
        self.config = config
        self.on_load = on_load

        layout = QVBoxLayout(self)
        self.list = QListWidget()
        layout.addWidget(self.list)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.addStretch()
        self.load_btn = QPushButton("Carregar")
        self.edit_btn = QPushButton("Editar")
        self.delete_btn = QPushButton("Remover")
        self.close_btn = QPushButton("Fechar")
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addWidget(btn_row)

        self.load_btn.clicked.connect(self._on_load)
        self.delete_btn.clicked.connect(self._on_delete)
        self.edit_btn.clicked.connect(self._on_edit)
        self.close_btn.clicked.connect(self.reject)

        self._refresh()

    def _refresh(self):
        self.list.clear()
        scs = self.config.get_saved_scenarios()
        for s in scs:
            it = QListWidgetItem(f"{s.get('name')} ({len(s.get('items',[]))} items)")
            it.setData(0, s)
            self.list.addItem(it)

    def _selected(self):
        it = self.list.currentItem()
        return it.data(0) if it else None

    def _on_load(self):
        s = self._selected()
        if not s:
            return
        # call handler and close
        try:
            self.on_load(s)
        except Exception:
            pass
        self.accept()

    def _on_delete(self):
        s = self._selected()
        if not s:
            return
        name = s.get("name")
        self.config.remove_scenario(name)
        self._refresh()
        try:
            if self.parent() and hasattr(self.parent(), 'append_signal'):
                self.parent().append_signal.emit(f"Cenário removido: {name}")
        except Exception:
            pass

    def _on_edit(self):
        s = self._selected()
        if not s:
            return
        from ui.edit_scenario_dialog import EditScenarioDialog
        d = EditScenarioDialog(self.config, s, parent=self)
        ok = d.exec()
        if ok:
            self._refresh()
            try:
                if self.parent() and hasattr(self.parent(), 'append_signal'):
                    self.parent().append_signal.emit(f"Cenário atualizado: {s.get('name')}")
            except Exception:
                pass
