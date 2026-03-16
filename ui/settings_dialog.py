from pathlib import Path
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
)

from core.config_manager import ConfigManager


class SettingsDialog(QDialog):
    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.config = config

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Caminho do repositório de automações Robot:"))
        self.path_edit = QLineEdit()
        layout.addWidget(self.path_edit)

        chooser_layout = QHBoxLayout()
        self.choose_btn = QPushButton("Selecionar pasta")
        self.choose_btn.clicked.connect(self._choose_folder)
        chooser_layout.addWidget(self.choose_btn)
        # Resource base picker
        layout.addWidget(QLabel("Resource base do Robot (opcional):"))
        self.resource_edit = QLineEdit()
        layout.addWidget(self.resource_edit)

        res_choose_layout = QHBoxLayout()
        self.choose_res_btn = QPushButton("Selecionar arquivo Resource")
        self.choose_res_btn.clicked.connect(self._choose_file)
        res_choose_layout.addWidget(self.choose_res_btn)
        layout.addLayout(res_choose_layout)
        layout.addLayout(chooser_layout)

        save_layout = QHBoxLayout()
        self.save_btn = QPushButton("Salvar")
        self.save_btn.clicked.connect(self._on_save)
        save_layout.addWidget(self.save_btn)
        layout.addLayout(save_layout)

        # load existing
        repo = self.config.get_repository_path()
        if repo:
            self.path_edit.setText(repo)
        base = self.config.get_base_resource_path()
        if base:
            self.resource_edit.setText(base)

    def _choose_folder(self):
        selected = QFileDialog.getExistingDirectory(self, "Selecionar pasta do repositório")
        if selected:
            self.path_edit.setText(selected)

    def _choose_file(self):
        selected, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo Resource", filter="Robot files (*.robot *.resource);;All files (*)")
        if selected:
            self.resource_edit.setText(selected)

    def _on_save(self):
        p = self.path_edit.text().strip()
        if p:
            # store as string
            self.config.set_repository_path(p)
        bp = self.resource_edit.text().strip()
        if bp:
            self.config.set_base_resource_path(bp)
        self.accept()
