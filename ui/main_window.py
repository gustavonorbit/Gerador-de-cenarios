"""
Simplified Main Window for manual suite assembly (V1)

This version removes automatic detection of runners/arguments and provides
an interface for the user to type keywords manually and build a small suite.
"""
from pathlib import Path
from typing import Optional
import threading
import time

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QSizePolicy,
    QCheckBox,
)
from PySide6.QtCore import Signal

from core.config_manager import ConfigManager
from ui.console_panel import ConsolePanel
from ui.settings_dialog import SettingsDialog
from ui.execution_window import ExecutionWindow
from core.suite_builder import build_temp_suite
from core.robot_executor import RobotExecutor


class MainWindow(QMainWindow):
    append_signal = Signal(str)

    def __init__(self, project_root: Optional[Path] = None):
        super().__init__()
        self.setWindowTitle("Robot Scenario Runner - V1 Manual Suite")

        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config = ConfigManager(self.project_root)

        # UI Widgets
        self.console = ConsolePanel()
        self.append_signal.connect(self._handle_output_line)

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # Top: settings button
        top_layout = QHBoxLayout()
        self.settings_btn = QPushButton("Configurações")
        self.settings_btn.clicked.connect(self._open_settings)
        top_layout.addWidget(self.settings_btn)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # Manual suite assembly area
        main_layout.addWidget(QLabel("Adicionar keyword manualmente (máx 5):"))
        kw_layout = QHBoxLayout()
        self.keyword_edit = QLineEdit()
        self.add_kw_btn = QPushButton("Adicionar keyword")
        self.add_kw_btn.clicked.connect(self._on_add_keyword)
        kw_layout.addWidget(self.keyword_edit)
        kw_layout.addWidget(self.add_kw_btn)
        main_layout.addLayout(kw_layout)

        # List of keywords
        self.kw_list = QListWidget()
        self.kw_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        main_layout.addWidget(QLabel("Suite montada:"))
        main_layout.addWidget(self.kw_list)

        # Execution controls
        exec_layout = QHBoxLayout()
        self.show_ui_chk = QCheckBox("Mostrar tela da automação")
        exec_layout.addWidget(self.show_ui_chk)

        self.open_exec_btn = QPushButton("Abrir tela de execução")
        self.open_exec_btn.clicked.connect(self._open_execution_window)
        self.run_btn = QPushButton("Executar")
        self.run_btn.clicked.connect(self._on_execute_clicked)
        exec_layout.addWidget(self.open_exec_btn)
        exec_layout.addWidget(self.run_btn)
        main_layout.addLayout(exec_layout)

        # Console
        main_layout.addWidget(QLabel("Console"))
        main_layout.addWidget(self.console, stretch=1)

        self.setCentralWidget(central)

    def _open_settings(self):
        dlg = SettingsDialog(self.config, parent=self)
        dlg.exec()

    def _on_add_keyword(self):
        text = self.keyword_edit.text().strip()
        if not text:
            self.console.append_text("Não é possível adicionar keyword vazia")
            return
        if self.kw_list.count() >= 5:
            self.console.append_text("Limite de 5 keywords atingido")
            return
        self.kw_list.addItem(text)
        self.keyword_edit.clear()

    def _open_execution_window(self):
        kws = [self.kw_list.item(i).text() for i in range(self.kw_list.count())]
        win = ExecutionWindow("Suite Manual", kws, parent=self)
        # Mirror console messages into the execution window when opened
        # For now we do not stream live logs automatically; the window is a simple view
        win.exec()

    def _on_execute_clicked(self):
        repo = self.config.get_repository_path()
        if not repo:
            self.console.append_text("Erro: caminho do repositório não configurado. Abra Configurações.")
            return
        if self.kw_list.count() == 0:
            self.console.append_text("Erro: nenhuma keyword adicionada à suite.")
            return
        # Gather keywords
        kws = [self.kw_list.item(i).text() for i in range(self.kw_list.count())]

        # Build temporary suite (include base resource if configured)
        base_res = self.config.get_base_resource_path()
        resource_arg = None
        if base_res:
            repo_path = Path(repo).resolve()
            base_cfg = base_res.strip()
            base_p = Path(base_cfg)

            # If relative path provided, normalize against repo and avoid duplicated repo folder
            if not base_p.is_absolute():
                parts = base_p.parts
                if parts and parts[0] == repo_path.name:
                    # remove the duplicated leading folder name
                    if len(parts) > 1:
                        base_p = Path(*parts[1:])
                    else:
                        base_p = Path('.')
                abs_path = (repo_path / base_p).resolve()
                if not abs_path.exists():
                    self.console.append_text(f"Erro: resource base não encontrado: {abs_path}")
                    return
                # use relative path to repo for Resource entry
                try:
                    rel = abs_path.relative_to(repo_path)
                    resource_arg = str(rel).replace('\\', '/')
                except Exception:
                    resource_arg = str(base_p).replace('\\', '/')
            else:
                # absolute path provided
                abs_path = base_p.resolve()
                if repo_path in abs_path.parents or abs_path == repo_path:
                    # convert to relative if inside repo
                    try:
                        rel = abs_path.relative_to(repo_path)
                        resource_arg = str(rel).replace('\\', '/')
                    except Exception:
                        resource_arg = str(abs_path)
                else:
                    resource_arg = str(abs_path)

        try:
            temp_path = build_temp_suite(kws, repo_root=repo, resource_path=resource_arg)
            self.append_signal.emit("Iniciando execução...")
            self.append_signal.emit(f"Repositório: {repo}")
            show_ui_state = self.show_ui_chk.isChecked()
            self.append_signal.emit(f"Mostrar tela: {'ativado' if show_ui_state else 'desativado'}")
            self.append_signal.emit(f"Suite temporária gerada: {temp_path}")
        except Exception as e:
            self.append_signal.emit(f"Erro ao gerar suite temporária: {e}")
            return

        def _run_real():
            executor = RobotExecutor()
            params = {"SHOW_UI": "True" if self.show_ui_chk.isChecked() else "False"}

            def _cb(line: str):
                # Forward Robot stdout lines to UI console
                try:
                    self.append_signal.emit(line)
                except Exception:
                    pass

            try:
                code = executor.run(temp_path, params, _cb, working_dir=repo)
                if code == 0:
                    self.append_signal.emit("Execução finalizada com sucesso")
                else:
                    self.append_signal.emit(f"Execução finalizada com código de saída: {code}")
            except Exception as e:
                self.append_signal.emit(f"Falha na execução: {e}")

        t = threading.Thread(target=_run_real, daemon=True)
        t.start()

    def _handle_output_line(self, line: str):
        self.console.append_text(line)

