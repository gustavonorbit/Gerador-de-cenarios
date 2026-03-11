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

    def _choose_folder(self):
        selected = QFileDialog.getExistingDirectory(self, "Selecionar pasta do repositório")
        if selected:
            self.path_edit.setText(selected)

    def _on_save(self):
        p = self.path_edit.text().strip()
        if p:
            # store as string
            self.config.set_repository_path(p)
        self.accept()
