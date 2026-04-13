"""Main window refactored for automatic project root detection,
indexing and keyword search.

Behavior changes:
- Detects project root automatically (where the app is located).
- Indexes .robot and .resource files on startup.
- Removes manual repository/resource settings.
"""
from pathlib import Path
from typing import Optional, Dict, List
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
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFileDialog, QListWidgetItem

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

        # application root (where this tool lives) — config.json stored here
        self.app_root = Path(__file__).resolve().parent.parent
        self.config = ConfigManager(self.app_root)

        # automation_root is chosen by the user (persisted)
        saved = self.config.get_automation_root_path()
        if saved:
            saved_p = Path(saved)
            if saved_p.exists():
                self.automation_root: Optional[Path] = saved_p.resolve()
            else:
                self.automation_root = None
                # notify user via console after UI set up
        else:
            self.automation_root = None

        # Keyword finder will be instantiated when an automation root is present
        self.finder: Optional[KeywordFinder] = None

        # UI Widgets
        self.console = ConsolePanel()
        self.append_signal.connect(self._handle_output_line)

        self._setup_ui()

        # If we have a saved automation root, initialize finder and index
        if self.automation_root:
            self.append_signal.emit(f"Raiz da automação carregada: {self.automation_root}")
            self._set_finder_and_index(self.automation_root)
        else:
            self.append_signal.emit("Nenhuma raiz de automação configurada. Selecione uma pasta para começar.")

    def _setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # Top info
        top_layout = QHBoxLayout()
        self.root_label = QLabel("Raiz ativa: (nenhuma)")
        top_layout.addWidget(self.root_label)
        top_layout.addStretch()
        self.select_root_btn = QPushButton("Selecionar raiz da automação")
        self.select_root_btn.clicked.connect(self._choose_automation_root)
        top_layout.addWidget(self.select_root_btn)
        self.reindex_btn = QPushButton("Reindexar")
        self.reindex_btn.clicked.connect(self._on_reindex_clicked)
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
        meta = item.data(Qt.UserRole)
        if not meta:
            return
        name = meta.get("name")
        kind = meta.get("kind")
        path = meta.get("path")
        if self.kw_list.count() >= 50:
            self.console.append_text("Limite de 50 itens atingido")
            return
        li = QListWidgetItem(f"{name} [{kind}] ({Path(path).name})")
        li.setData(Qt.UserRole, meta)
        self.kw_list.addItem(li)
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
        # collect items from kw_list (they contain meta in UserRole)
        keyword_items = []
        test_map: Dict[str, List[str]] = {}
        for i in range(self.kw_list.count()):
            item = self.kw_list.item(i)
            meta = item.data(Qt.UserRole)
            if not meta:
                continue
            if meta.get("kind") == "keyword":
                keyword_items.append(meta)
            else:
                file = meta.get("path")
                test_map.setdefault(file, []).append(meta.get("name"))

        executor = RobotExecutor()
        params_common = {"SHOW_UI": "True" if self.show_ui_chk.isChecked() else "False"}

        def _cb(line: str):
            try:
                self.append_signal.emit(line)
            except Exception:
                pass

        def _run_all():
            # run keywords (single temp suite) if present
            try:
                if keyword_items:
                    kws = [m["name"] for m in keyword_items]
                    resource_files = []
                    for m in keyword_items:
                        f = m.get("path")
                        if f and f not in resource_files:
                            resource_files.append(f)
                    temp_path = build_temp_suite(kws, repo_root=self.automation_root or self.app_root, resource_paths=resource_files if resource_files else None)
                    self.append_signal.emit("Iniciando execução (keywords)...")
                    code = executor.run(temp_path, dict(params_common), _cb, working_dir=str(self.automation_root or self.app_root))
                    self.append_signal.emit(f"Execução keywords finalizada com código: {code}")

                # run tests grouped by file
                for file, tests in test_map.items():
                    self.append_signal.emit(f"Iniciando execução de testes em: {file}")
                    params = dict(params_common)
                    params["__tests__"] = tests
                    code = executor.run(file, params, _cb, working_dir=str(self.automation_root or self.app_root))
                    self.append_signal.emit(f"Execução {Path(file).name} finalizada com código: {code}")
            except Exception as e:
                self.append_signal.emit(f"Falha na execução: {e}")

        t = threading.Thread(target=_run_all, daemon=True)
        t.start()

    def _handle_output_line(self, line: str):
        self.console.append_text(line)

    # --- indexing and search handlers ---
    def _index_project(self):
        if not self.finder:
            return
        try:
            k_count, t_count = self.finder.index()
            self.append_signal.emit(f"Projeto indexado com sucesso. {k_count} keywords e {t_count} testes encontrados.")
        except Exception as e:
            self.append_signal.emit(f"Erro na indexação: {e}")

    def _on_search_text_changed(self, text: str):
        try:
            self.suggestion_list.clear()
            if not self.finder:
                return
            results = self.finder.search(text)
            for name, kind in results:
                files = self.finder.get_files_for(name, kind)
                file_display = files[0] if files else ""
                display = f"{name} [{kind}] ({Path(file_display).name})"
                it = QListWidgetItem(display)
                it.setData(Qt.UserRole, {"name": name, "kind": kind, "path": file_display})
                self.suggestion_list.addItem(it)
        except Exception:
            pass

    def _on_suggestion_double(self, item):
        if not item:
            return
        meta = item.data(Qt.UserRole)
        if not meta:
            return
        if self.kw_list.count() >= 50:
            self.console.append_text("Limite de 50 itens atingido")
            return
        li = QListWidgetItem(item.text())
        li.setData(Qt.UserRole, meta)
        self.kw_list.addItem(li)

    # --- automation root selection / persistence ---
    def _choose_automation_root(self):
        selected = QFileDialog.getExistingDirectory(self, "Selecionar raiz da automação")
        if not selected:
            return
        p = Path(selected).resolve()
        if not p.exists():
            self.append_signal.emit(f"Caminho selecionado não existe: {p}")
            return
        self.config.set_automation_root_path(str(p))
        self.automation_root = p
        self.append_signal.emit(f"Raiz da automação carregada: {p}")
        self._set_finder_and_index(p)

    def _set_finder_and_index(self, root: Path):
        try:
            self.finder = KeywordFinder(root)
            self.root_label.setText(f"Raiz ativa: {root}")
            threading.Thread(target=self._index_project, daemon=True).start()
        except Exception as e:
            self.append_signal.emit(f"Erro ao inicializar indexador: {e}")

    def _on_reindex_clicked(self):
        if not self.automation_root:
            self.append_signal.emit("Nenhuma raiz configurada para reindexar")
            return
        threading.Thread(target=self._index_project, daemon=True).start()

