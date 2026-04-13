"""Main window refactored for automatic project root detection,
indexing and keyword search.

Behavior changes:
- Detects project root automatically (where the app is located).
- Indexes .robot and .resource files on startup.
- Removes manual repository/resource settings.
"""
from pathlib import Path
from typing import Optional
import threading

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
from core.keyword_finder import KeywordFinder
from ui.console_panel import ConsolePanel
from ui.execution_window import ExecutionWindow
from core.suite_builder import build_temp_suite
from core.robot_executor import RobotExecutor


class MainWindow(QMainWindow):
    append_signal = Signal(str)

    def __init__(self, project_root: Optional[Path] = None):
        super().__init__()
        self.setWindowTitle("Robot Scenario Runner")

        # Determine project root automatically: two levels up from this file
        if project_root is None:
            # main_window.py is in ui/; project root is parent of ui/
            self.project_root = Path(__file__).resolve().parent.parent
        else:
            self.project_root = Path(project_root).resolve()

        self.config = ConfigManager(self.project_root)

        # Keyword finder indexes robot files automatically
        self.finder = KeywordFinder(self.project_root)

        # UI Widgets
        self.console = ConsolePanel()
        self.append_signal.connect(self._handle_output_line)

        self._setup_ui()

        # Start indexing in background
        self.append_signal.emit(f"Raiz do projeto detectada automaticamente: {self.project_root}")
        self.append_signal.emit("Iniciando indexação do projeto...")
        t = threading.Thread(target=self._index_project, daemon=True)
        t.start()

    def _setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # Top info
        top_layout = QHBoxLayout()
        self.root_label = QLabel(f"Raiz: {self.project_root}")
        top_layout.addWidget(self.root_label)
        top_layout.addStretch()
        self.reindex_btn = QPushButton("Reindexar")
        self.reindex_btn.clicked.connect(lambda: threading.Thread(target=self._index_project, daemon=True).start())
        top_layout.addWidget(self.reindex_btn)
        main_layout.addLayout(top_layout)

        # Search area for keywords
        main_layout.addWidget(QLabel("Buscar keyword:"))
        kw_layout = QHBoxLayout()
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("Digite para buscar keywords...")
        self.keyword_edit.textChanged.connect(self._on_search_text_changed)
        self.add_kw_btn = QPushButton("Adicionar selecionada")
        self.add_kw_btn.clicked.connect(self._on_add_selected_suggestion)
        kw_layout.addWidget(self.keyword_edit)
        kw_layout.addWidget(self.add_kw_btn)
        main_layout.addLayout(kw_layout)

        # Suggestions list
        self.suggestion_list = QListWidget()
        self.suggestion_list.itemDoubleClicked.connect(self._on_suggestion_double)
        main_layout.addWidget(QLabel("Sugestões:"))
        main_layout.addWidget(self.suggestion_list)

        # List of keywords (the assembled suite)
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
        # settings dialog removed - no manual path configuration
        self.console.append_text("Tela de Configurações removida: caminhos são detectados automaticamente")

    def _on_add_selected_suggestion(self):
        item = self.suggestion_list.currentItem()
        if not item:
            self.console.append_text("Nenhuma sugestão selecionada")
            return
        text = item.text().split(' — ')[0].strip()
        if not text:
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
        if self.kw_list.count() == 0:
            self.console.append_text("Erro: nenhuma keyword adicionada à suite.")
            return

        kws = [self.kw_list.item(i).text() for i in range(self.kw_list.count())]

        # Determine resource files automatically from index
        resource_files = []
        for k in kws:
            files = self.finder.get_files_for_keyword(k)
            for f in files:
                if f not in resource_files:
                    resource_files.append(f)

        try:
            temp_path = build_temp_suite(kws, repo_root=self.project_root, resource_paths=resource_files if resource_files else None)
            self.append_signal.emit("Iniciando execução...")
            self.append_signal.emit(f"Raiz do projeto: {self.project_root}")
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
                try:
                    self.append_signal.emit(line)
                except Exception:
                    pass

            try:
                code = executor.run(temp_path, params, _cb, working_dir=str(self.project_root))
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

    # --- indexing and search handlers ---
    def _index_project(self):
        try:
            count = self.finder.index()
            self.append_signal.emit(f"Projeto indexado com sucesso. {count} keywords encontradas.")
        except Exception as e:
            self.append_signal.emit(f"Erro na indexação: {e}")

    def _on_search_text_changed(self, text: str):
        try:
            results = self.finder.search(text)
            self.suggestion_list.clear()
            for r in results:
                files = self.finder.get_files_for_keyword(r)
                file_display = files[0] if files else ""
                self.suggestion_list.addItem(f"{r} — {Path(file_display).name}")
        except Exception:
            # on search errors, keep UI usable
            pass

    def _on_suggestion_double(self, item):
        if not item:
            return
        text = item.text().split(' — ')[0].strip()
        if not text:
            return
        if self.kw_list.count() >= 5:
            self.console.append_text("Limite de 5 keywords atingido")
            return
        self.kw_list.addItem(text)

