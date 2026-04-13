from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from typing import Optional


class FavoritesDialog(QDialog):
    def __init__(self, config, parent: Optional[object] = None):
        super().__init__(parent)
        self.setWindowTitle("Favoritos")
        self.config = config
        self.parent = parent

        self.layout = QVBoxLayout(self)
        self.list_w = QListWidget()
        self.list_w.itemActivated.connect(self._on_item_activated)
        self.layout.addWidget(self.list_w)

        self._refresh()

    def _refresh(self):
        self.list_w.clear()
        favs = self.config.get_favorites() or []
        for f in favs:
            name = f.get("name")
            typ = f.get("type")
            file = f.get("file")
            li = QListWidgetItem()
            meta = {"name": name, "kind": typ, "path": file, "file": file, "type": typ}
            li.setData(Qt.UserRole, meta)
            self.list_w.addItem(li)
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(4, 2, 4, 2)
            lbl = QLabel(f"{name} ({typ}) - {file}")
            h.addWidget(lbl)
            rem = QPushButton("Remover")

            def _make_remove(m=meta, item=li):
                def _remove():
                    try:
                        self.config.remove_favorite({"name": m.get("name"), "type": m.get("kind"), "file": m.get("file")})
                        # remove from list widget
                        self.list_w.takeItem(self.list_w.row(item))
                        if hasattr(self.parent, 'append_signal'):
                            try:
                                self.parent.append_signal.emit(f"Favorito removido: {m.get('name')}")
                            except Exception:
                                pass
                        if hasattr(self.parent, '_refresh_favorites_ui'):
                            try:
                                self.parent._refresh_favorites_ui()
                            except Exception:
                                pass
                    except Exception:
                        pass
                return _remove

            rem.clicked.connect(_make_remove())
            h.addWidget(rem)
            self.list_w.setItemWidget(li, w)

    def _on_item_activated(self, item: QListWidgetItem):
        meta = item.data(Qt.UserRole)
        if not meta:
            return
        # add to suite via parent
        if self.parent and hasattr(self.parent, '_add_meta_to_suite'):
            try:
                self.parent._add_meta_to_suite(meta)
                if hasattr(self.parent, 'append_signal'):
                    try:
                        self.parent.append_signal.emit(f"Favorito adicionado à suite: {meta.get('name')}")
                    except Exception:
                        pass
            except Exception:
                pass
