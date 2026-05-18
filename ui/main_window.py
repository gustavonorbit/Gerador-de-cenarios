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
    QTabWidget,
    QComboBox,
    QSizePolicy,
    QCheckBox,
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtWidgets import QFileDialog, QListWidgetItem

from core.config_manager import ConfigManager
from core.app_info import APP_VERSION
from core.keyword_finder import KeywordFinder
from ui.keyword_arguments_dialog import KeywordArgumentsDialog
from ui.console_panel import ConsolePanel
from ui.execution_window import ExecutionWindow
from core.suite_builder import build_temp_suite
from core.robot_executor import RobotExecutor


class MainWindow(QMainWindow):
    append_signal = Signal(str)
    ui_signal = Signal(str)
    MAX_SUITE_ITEMS = 5
    SUGGESTION_ITEM_HEIGHT = 30
    SUGGESTION_TEXT_LIMIT = 120

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
        self.module_lists: Dict[str, QListWidget] = {}
        self._suppress_filter_logs = False

        # UI Widgets
        self.console = ConsolePanel()
        self.ui_signal.connect(self._handle_ui_command)
        self.append_signal.connect(self._handle_output_line)

        self._setup_ui()

        # If we have a saved automation root, initialize finder and index
        if self.automation_root:
            self.append_signal.emit(f"Raiz da automação carregada: {self.automation_root}")
            self._set_finder_and_index(self.automation_root)
        else:
            self.append_signal.emit("Nenhuma raiz de automação configurada. Selecione uma pasta para começar.")
        # load favorites into UI
        try:
            self._refresh_favorites_ui()
        except Exception:
            pass
        self.current_executor = None

        # wire save scenario button state and saved scenarios button
        try:
            # update enable state when items change
            self.kw_list.model().rowsInserted.connect(lambda *_: self._update_save_button_state())
            self.kw_list.model().rowsRemoved.connect(lambda *_: self._update_save_button_state())
            self.save_scenario_btn.clicked.connect(self._on_save_scenario_clicked)
            self.saved_scenarios_btn.clicked.connect(self._open_saved_scenarios)
        except Exception:
            pass

    def _setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # Top info
        top_layout = QHBoxLayout()
        self.root_label = QLabel("Raiz ativa: (nenhuma)")
        top_layout.addWidget(self.root_label)
        top_layout.addStretch()
        self.version_label = QLabel(f"Versão {APP_VERSION}")
        top_layout.addWidget(self.version_label)
        self.select_root_btn = QPushButton("Selecionar raiz da automação")
        self.select_root_btn.clicked.connect(self._choose_automation_root)
        top_layout.addWidget(self.select_root_btn)
        # Favorites button (replaces Reindexar)
        self.favorites_btn = QPushButton("Favoritos")
        self.favorites_btn.clicked.connect(self._open_favorites)
        top_layout.addWidget(self.favorites_btn)
        # Saved scenarios button
        self.saved_scenarios_btn = QPushButton("Cenários Salvos")
        self.saved_scenarios_btn.clicked.connect(self._open_saved_scenarios)
        top_layout.addWidget(self.saved_scenarios_btn)
        main_layout.addLayout(top_layout)

        # Search/filter area for indexed keywords and tests
        main_layout.addWidget(QLabel("Buscar keyword/teste:"))
        kw_layout = QHBoxLayout()
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("Digite para filtrar keywords e testes...")
        self.keyword_edit.textChanged.connect(self._on_search_text_changed)
        self.add_kw_btn = QPushButton("Adicionar selecionada")
        self.add_kw_btn.clicked.connect(self._on_add_selected_suggestion)
        self.favorite_selected_btn = QPushButton("Favoritar")
        self.favorite_selected_btn.setFixedWidth(80)
        self.favorite_selected_btn.clicked.connect(self._toggle_selected_favorite)
        kw_layout.addWidget(self.keyword_edit)
        kw_layout.addWidget(self.add_kw_btn)
        kw_layout.addWidget(self.favorite_selected_btn)
        main_layout.addLayout(kw_layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Tipo:"))
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItems(["Todos", "Somente Keywords", "Somente Testes"])
        self.type_filter_combo.currentTextChanged.connect(self._on_type_filter_changed)
        filter_layout.addWidget(self.type_filter_combo)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Suggestions grouped by module
        self.suggestion_tabs = QTabWidget()
        self.suggestion_tabs.currentChanged.connect(self._on_module_tab_changed)
        main_layout.addWidget(QLabel("Itens disponíveis:"))
        main_layout.addWidget(self.suggestion_tabs)

        # (Favorites moved to separate dialog) suggestions area expands

        # List of keywords (the assembled suite)
        self.kw_list = QListWidget()
        self.kw_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # header for suite area with a '+' save scenario button
        suite_header = QWidget()
        sh_layout = QHBoxLayout(suite_header)
        sh_layout.setContentsMargins(0, 0, 0, 0)
        sh_layout.addWidget(QLabel("Suite montada:"))
        sh_layout.addStretch()
        self.save_scenario_btn = QPushButton("+")
        self.save_scenario_btn.setEnabled(False)
        self.save_scenario_btn.setFixedWidth(30)
        sh_layout.addWidget(self.save_scenario_btn)
        main_layout.addWidget(suite_header)
        main_layout.addWidget(self.kw_list)

        # Execution controls
        exec_layout = QHBoxLayout()

        # Automation type selector (Desktop / Web)
        self.automation_type_label = QLabel("Tipo de automação:")
        exec_layout.addWidget(self.automation_type_label)
        self.automation_type_combo = QComboBox()
        self.automation_type_combo.addItems(["Desktop", "Web"])
        self.automation_type_combo.setCurrentText("Desktop")
        self.automation_type_combo.currentTextChanged.connect(self._on_automation_type_changed)
        exec_layout.addWidget(self.automation_type_combo)

        # Show UI checkbox (relevant for Web)
        self.show_ui_chk = QCheckBox("Mostrar tela da automação (Web)")
        # default: Desktop mode -> hide web-only control
        self.show_ui_chk.setVisible(False)
        exec_layout.addWidget(self.show_ui_chk)

        # Execution DB selection (relevant for Desktop)
        self.db_label = QLabel("Base de execução:")
        exec_layout.addWidget(self.db_label)
        self.db_combo = QComboBox()
        self.db_combo.addItems(["SQL", "SAP", "ORACLE"])
        self.db_combo.setCurrentText("SQL")
        self.db_combo.currentTextChanged.connect(self._on_database_filter_changed)
        exec_layout.addWidget(self.db_combo)

        self.open_exec_btn = QPushButton("Abrir tela de execução")
        self.open_exec_btn.clicked.connect(self._open_execution_window)
        self.run_btn = QPushButton("Executar")
        self.run_btn.clicked.connect(self._on_execute_clicked)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setVisible(False)
        exec_layout.addWidget(self.open_exec_btn)
        exec_layout.addWidget(self.run_btn)
        exec_layout.addWidget(self.stop_btn)
        main_layout.addLayout(exec_layout)

        # Console
        main_layout.addWidget(QLabel("Console"))
        main_layout.addWidget(self.console, stretch=1)

        self.setCentralWidget(central)

    def _on_automation_type_changed(self, value: str) -> None:
        try:
            if value == "Desktop":
                # Desktop: show DB selector, hide web-only UI checkbox
                self.db_label.setVisible(True)
                self.db_combo.setVisible(True)
                self.show_ui_chk.setVisible(False)
            else:
                # Web: hide DB selector, show web-only UI checkbox
                self.db_label.setVisible(False)
                self.db_combo.setVisible(False)
                self.show_ui_chk.setVisible(True)
        except Exception:
            pass

    def _open_settings(self):
        # settings dialog removed - no manual path configuration
        self.console.append_text("Tela de Configurações removida: caminhos são detectados automaticamente")

    def _on_add_selected_suggestion(self):
        current_list = self._current_suggestion_list()
        item = current_list.currentItem() if current_list else None
        if not item:
            self.console.append_text("Nenhuma sugestão selecionada")
            return
        meta = item.data(Qt.UserRole)
        if not meta:
            return
        try:
            self._handle_add_meta_with_args(meta)
        finally:
            self.keyword_edit.clear()

    def _add_meta_to_suite(self, meta: dict) -> None:
        if not meta:
            return
        if self.kw_list.count() >= self.MAX_SUITE_ITEMS:
            self.console.append_text(f"Limite de {self.MAX_SUITE_ITEMS} itens atingido")
            return
        name = meta.get("name")
        kind = meta.get("kind") or meta.get("type")
        path = meta.get("path") or meta.get("file")
        li = QListWidgetItem(f"{name} [{kind}]")
        li.setData(Qt.UserRole, meta)
        self.kw_list.addItem(li)
        self._set_item_widget(li, name, kind, path, meta)

    def _handle_add_meta_with_args(self, meta: dict) -> None:
        """If the selected meta is a keyword and has arguments, prompt the user.

        Adds meta to suite with `argument_names` and `arguments` populated when confirmed.
        """
        if not meta:
            return
        name = meta.get("name")
        kind = meta.get("kind") or meta.get("type")
        path = meta.get("path") or meta.get("file")

        # Only keywords can have arguments in this scope
        if kind != "keyword" or not self.finder:
            # add as-is
            self._add_meta_to_suite(meta)
            return

        try:
            arg_names = self.finder.get_keyword_arguments(name, file_path=path)
        except Exception:
            arg_names = []

        if not arg_names:
            # no args, add immediately
            self.append_signal.emit(f"Keyword adicionada à suite: {name}")
            self._add_meta_to_suite(meta)
            return

        # has args -> ask user
        self.append_signal.emit(f"Keyword selecionada possui argumentos: {name}")
        values = KeywordArgumentsDialog.get_arguments(self, name, arg_names)
        if values is None:
            self.append_signal.emit(f"Adição cancelada pelo usuário: {name}")
            return

        # attach ordered names and values
        meta['argument_names'] = list(arg_names)
        meta['arguments'] = {k: values.get(k, "") for k in arg_names}
        self.append_signal.emit(f"Keyword adicionada à suite com argumentos: {name}")
        self._add_meta_to_suite(meta)

    def _on_favorite_double(self, item: QListWidgetItem) -> None:
        if not item:
            return
        meta = item.data(Qt.UserRole)
        if not meta:
            return
        self._add_meta_to_suite(meta)

    def _update_save_button_state(self):
        try:
            self.save_scenario_btn.setEnabled(self.kw_list.count() > 0)
        except Exception:
            pass

    def _on_save_scenario_clicked(self):
        from ui.save_scenario_dialog import SaveScenarioDialog
        d = SaveScenarioDialog(self)
        ok = d.exec()
        if not ok:
            return
        name = d.get_name()
        if not name:
            return
        items = []
        for i in range(self.kw_list.count()):
            item = self.kw_list.item(i)
            meta = item.data(Qt.UserRole) or {}
            it = {
                'name': meta.get('name'),
                'type': meta.get('kind') or meta.get('type'),
                'file': meta.get('path') or meta.get('file'),
                'argument_names': meta.get('argument_names') or [],
                'arguments': meta.get('arguments') or {}
            }
            items.append(it)
        scenario = {'name': name, 'items': items}
        try:
            self.config.add_or_update_scenario(scenario)
            self.append_signal.emit(f"Cenário salvo: {name}")
        except Exception as e:
            self.append_signal.emit(f"Falha ao salvar cenário: {e}")

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
        # keep reference so Stop can call executor.stop()
        self.current_executor = executor
        # params will be built per-run depending on automation type (Desktop/Web)
        # See _on_automation_type_changed for UI behavior
        

        def _cb(line: str):
            try:
                self.append_signal.emit(line)
            except Exception:
                pass

        def _run_all():
            # run keywords (single temp suite) if present
            try:
                # Log and pass CURRENT_DB
                # Determine automation type and log
                try:
                    automation_type = (self.automation_type_combo.currentText() if hasattr(self, 'automation_type_combo') else 'Desktop') or 'Desktop'
                except Exception:
                    automation_type = 'Desktop'
                self.append_signal.emit(f"Tipo de automação selecionado: {automation_type}")

                if automation_type == 'Desktop':
                    try:
                        current_db = (self.db_combo.currentText() if hasattr(self, 'db_combo') else None) or "SQL"
                    except Exception:
                        current_db = "SQL"
                    self.append_signal.emit(f"Base de execução selecionada: {current_db}")
                else:
                    show_ui_state = "ativado" if self.show_ui_chk.isChecked() else "desativado"
                    self.append_signal.emit(f"Mostrar tela da automação (Web): {show_ui_state}")

                try:
                    self.ui_signal.emit("execution_started")
                except Exception:
                    pass
                self.append_signal.emit("Execução iniciada")

                if keyword_items:
                    # pass the structured items (may include arguments) to suite builder
                    resource_files = []
                    for m in keyword_items:
                        f = m.get("path")
                        if f and f not in resource_files:
                            resource_files.append(f)
                    temp_path = build_temp_suite(keyword_items, repo_root=self.automation_root or self.app_root, resource_paths=resource_files if resource_files else None)
                    self.append_signal.emit("Iniciando execução (keywords)...")
                    # build params according to automation type
                    if automation_type == 'Desktop':
                        params = {"CURRENT_DB": current_db}
                    else:
                        params = {"SHOW_UI": "True" if self.show_ui_chk.isChecked() else "False"}
                    code = executor.run(temp_path, params, _cb, working_dir=str(self.automation_root or self.app_root))
                    self.append_signal.emit(f"Execução keywords finalizada com código: {code}")

                # run tests grouped by file
                for file, tests in test_map.items():
                    self.append_signal.emit(f"Iniciando execução de testes em: {file}")
                    if automation_type == 'Desktop':
                        params = {"CURRENT_DB": current_db}
                    else:
                        params = {"SHOW_UI": "True" if self.show_ui_chk.isChecked() else "False"}
                    params["__tests__"] = tests
                    code = executor.run(file, params, _cb, working_dir=str(self.automation_root or self.app_root))
                    self.append_signal.emit(f"Execução {Path(file).name} finalizada com código: {code}")
                    
            except Exception as e:
                self.append_signal.emit(f"Falha na execução: {e}")
            finally:
                try:
                    self.ui_signal.emit("execution_finished")
                except Exception:
                    pass
                self.append_signal.emit("Execução finalizada")
                try:
                    self.current_executor = None
                except Exception:
                    pass

        t = threading.Thread(target=_run_all, daemon=True)
        t.start()

    def _handle_ui_command(self, cmd: str):
        try:
            if cmd == "execution_started":
                self.stop_btn.setVisible(True)
                self.run_btn.setEnabled(False)
                self.open_exec_btn.setEnabled(False)
            elif cmd in ("execution_finished", "execution_stopped"):
                self.stop_btn.setVisible(False)
                self.stop_btn.setEnabled(True)
                self.run_btn.setEnabled(True)
                self.open_exec_btn.setEnabled(True)
            elif cmd == "index_finished":
                self._refresh_suggestions()
                self._log_current_filters()
        except Exception:
            pass

    def _on_stop_clicked(self):
        # disable stop button immediately
        try:
            self.stop_btn.setEnabled(False)
            if self.current_executor:
                self.current_executor.stop()
            self.append_signal.emit("Execução interrompida pelo usuário.")
            try:
                self.ui_signal.emit("execution_stopped")
            except Exception:
                pass
        except Exception as e:
            self.append_signal.emit(f"Falha ao interromper execução: {e}")

    def _open_favorites(self):
        try:
            from ui.favorites_dialog import FavoritesDialog
            d = FavoritesDialog(self.config, parent=self)
            d.exec()
        except Exception as e:
            self.append_signal.emit(f"Erro abrindo Favoritos: {e}")

    def _open_saved_scenarios(self):
        try:
            from ui.saved_scenarios_dialog import SavedScenariosDialog
            d = SavedScenariosDialog(self.config, on_load=self._load_scenario, parent=self)
            d.exec()
        except Exception as e:
            self.append_signal.emit(f"Erro abrindo Cenários Salvos: {e}")

    def _load_scenario(self, scenario: dict) -> None:
        # replace current suite with scenario items
        try:
            self.kw_list.clear()
            for it in scenario.get('items', []):
                meta = {
                    'name': it.get('name'),
                    'kind': it.get('type'),
                    'path': it.get('file'),
                    'argument_names': it.get('argument_names') or [],
                    'arguments': it.get('arguments') or {}
                }
                li = QListWidgetItem(f"{meta.get('name')} [{meta.get('kind') or meta.get('type')}]")
                li.setData(Qt.UserRole, meta)
                self.kw_list.addItem(li)
                self._set_item_widget(li, meta.get('name'), meta.get('kind') or meta.get('type'), meta.get('path') or meta.get('file'), meta)
            self.append_signal.emit(f"Cenário carregado: {scenario.get('name')}")
        except Exception as e:
            self.append_signal.emit(f"Falha ao carregar cenário: {e}")

    def _handle_output_line(self, line: str):
        self.console.append_text(line)

    def _set_item_widget(self, list_item: QListWidgetItem, name: str, kind: str, path: str, meta: dict):
        """Create a widget for the QListWidgetItem with label and remove button."""
        from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)

        # display argument preview if present
        arg_names = meta.get("argument_names") or []
        arguments = meta.get("arguments") or {}
        file_name = Path(path).name if path else ""
        if arg_names:
            preview = ", ".join(f"{n}={arguments.get(n,'')}" for n in arg_names)
            label = QLabel(f"{name} ({len(arg_names)} args) [{preview}] ({file_name})")
        else:
            label = QLabel(f"{name} [{kind}] ({file_name})")
        layout.addWidget(label)

        remove_btn = QPushButton("Remover")
        remove_btn.setFixedWidth(80)

        def _on_remove():
            # find and remove the QListWidgetItem
            try:
                row = self.kw_list.row(list_item)
                if row >= 0:
                    taken = self.kw_list.takeItem(row)
                    # explicit deletion of widget
                    widget.deleteLater()
                    self.append_signal.emit(f"Item removido da suite: {name}")
            except Exception:
                pass

        remove_btn.clicked.connect(_on_remove)
        layout.addWidget(remove_btn)

        self.kw_list.setItemWidget(list_item, widget)

    def _refresh_favorites_ui(self):
        # Favorites are shown in a separate dialog; refresh suggestion stars
        try:
            self._refresh_suggestions()
        except Exception:
            pass

    # --- indexing and search handlers ---
    def _index_project(self):
        if not self.finder:
            return
        try:
            k_count, t_count = self.finder.index()
            self.append_signal.emit(f"Projeto indexado com sucesso. {k_count} keywords e {t_count} testes encontrados.")
            modules = ", ".join(self.finder.detected_modules()) or "nenhum"
            databases = ", ".join(self.finder.detected_database_scopes()) or "nenhuma"
            self.append_signal.emit(f"Módulos detectados: {modules}")
            self.append_signal.emit(f"Bases detectadas: {databases}")
            self.ui_signal.emit("index_finished")
        except Exception as e:
            self.append_signal.emit(f"Erro na indexação: {e}")

    def _on_search_text_changed(self, text: str):
        self._refresh_suggestions()

    def _on_database_filter_changed(self, value: str):
        try:
            if not self._suppress_filter_logs:
                self.append_signal.emit(f"Filtro aplicado: base {value}")
            self._refresh_suggestions()
        except Exception:
            pass

    def _on_type_filter_changed(self, value: str):
        try:
            if not self._suppress_filter_logs:
                self.append_signal.emit(f"Tipo exibido: {value}")
            self._refresh_suggestions()
        except Exception:
            pass

    def _on_module_tab_changed(self, index: int):
        try:
            if self._suppress_filter_logs or index < 0:
                return
            module = self.suggestion_tabs.tabText(index)
            if module:
                self.append_signal.emit(f"Módulo selecionado: {module}")
        except Exception:
            pass

    def _current_suggestion_list(self) -> Optional[QListWidget]:
        try:
            widget = self.suggestion_tabs.currentWidget()
            if isinstance(widget, QListWidget):
                return widget
        except Exception:
            pass
        return None

    def _current_database_filter(self) -> str:
        try:
            return self.db_combo.currentText() or "SQL"
        except Exception:
            return "SQL"

    def _current_type_filter_label(self) -> str:
        try:
            return self.type_filter_combo.currentText() or "Todos"
        except Exception:
            return "Todos"

    def _current_kind_filter(self) -> Optional[str]:
        value = self._current_type_filter_label()
        if value == "Somente Keywords":
            return "keyword"
        if value == "Somente Testes":
            return "test"
        return None

    def _log_current_filters(self) -> None:
        self.append_signal.emit(f"Filtro aplicado: base {self._current_database_filter()}")
        self.append_signal.emit(f"Tipo exibido: {self._current_type_filter_label()}")
        try:
            current_index = self.suggestion_tabs.currentIndex()
            if current_index >= 0:
                module = self.suggestion_tabs.tabText(current_index)
                if module:
                    self.append_signal.emit(f"Módulo selecionado: {module}")
        except Exception:
            pass

    def _refresh_suggestions(self):
        try:
            if not hasattr(self, "suggestion_tabs"):
                return

            previous_module = ""
            try:
                current_index = self.suggestion_tabs.currentIndex()
                if current_index >= 0:
                    previous_module = self.suggestion_tabs.tabText(current_index)
            except Exception:
                previous_module = ""

            self._suppress_filter_logs = True
            self.suggestion_tabs.clear()
            self.module_lists.clear()

            if not self.finder:
                return

            query = self.keyword_edit.text() if hasattr(self, "keyword_edit") else ""
            database_scope = self._current_database_filter()
            kind_filter = self._current_kind_filter()
            modules = self.finder.modules_for(database_scope=database_scope, kind_filter=kind_filter)
            if not modules:
                modules = ["Geral"]

            results = self.finder.search_items(
                query,
                limit=None,
                database_scope=database_scope,
                kind_filter=kind_filter,
            )
            grouped: Dict[str, List[dict]] = {module: [] for module in modules}
            for meta in results:
                module = meta.get("module") or "Geral"
                grouped.setdefault(module, []).append(meta)

            for module in modules:
                module_list = QListWidget()
                module_list.setUniformItemSizes(True)
                module_list.setSpacing(1)
                module_list.itemDoubleClicked.connect(self._on_suggestion_double)
                self.module_lists[module] = module_list
                self.suggestion_tabs.addTab(module_list, module)

                for meta in grouped.get(module, []):
                    name = meta.get("name", "")
                    kind = meta.get("kind") or meta.get("type") or ""
                    file_display = meta.get("path") or meta.get("file") or ""
                    item = QListWidgetItem(f"{name} [{kind}]")
                    item.setData(Qt.UserRole, meta)
                    module_list.addItem(item)
                    self._set_suggestion_widget(item, name, kind, file_display, meta)

            if previous_module and previous_module in self.module_lists:
                self.suggestion_tabs.setCurrentIndex(modules.index(previous_module))
            elif modules:
                self.suggestion_tabs.setCurrentIndex(0)
        except Exception:
            pass
        finally:
            self._suppress_filter_logs = False

    def _on_suggestion_double(self, item):
        if not item:
            return
        meta = item.data(Qt.UserRole)
        if not meta:
            return
        # reuse add flow which handles arguments and limits
        if self.kw_list.count() >= self.MAX_SUITE_ITEMS:
            self.console.append_text(f"Limite de {self.MAX_SUITE_ITEMS} itens atingido")
            return
        try:
            self._handle_add_meta_with_args(meta)
        except Exception:
            pass

    def _set_suggestion_widget(self, list_item: QListWidgetItem, name: str, kind: str, path: str, meta: dict):
        list_item.setSizeHint(QSize(0, self.SUGGESTION_ITEM_HEIGHT))
        text = self._suggestion_item_text(name, kind, path, meta)
        list_item.setText(self._truncate_text(text, self.SUGGESTION_TEXT_LIMIT))
        list_item.setToolTip(self._suggestion_tooltip_text(name, kind, path, meta))

    def _suggestion_item_text(self, name: str, kind: str, path: str, meta: dict) -> str:
        star = "★" if self._is_favorite(name, kind, path) else "☆"
        file_label = self._suggestion_short_file_label(path, meta)
        return f"{star} {name} [{kind}] - {file_label}"

    def _suggestion_tooltip_text(self, name: str, kind: str, path: str, meta: dict) -> str:
        file_label = meta.get("relative_file") or path or ""
        return f"{name} [{kind}] ({file_label})"

    def _suggestion_short_file_label(self, path: str, meta: dict) -> str:
        relative_file = meta.get("relative_file") or ""
        if relative_file and len(relative_file) <= 80:
            return relative_file
        if path:
            return Path(path).name
        return relative_file

    def _truncate_text(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return f"{text[:max(0, limit - 3)]}..."

    def _is_favorite(self, name: str, kind: str, path: str) -> bool:
        favs = self.config.get_favorites()
        return any((f.get("name"), f.get("type"), f.get("file")) == (name, kind, path) for f in favs)

    def _toggle_selected_favorite(self):
        current_list = self._current_suggestion_list()
        item = current_list.currentItem() if current_list else None
        if not item:
            self.console.append_text("Nenhum item selecionado para favoritar")
            return

        meta = item.data(Qt.UserRole)
        if not meta:
            return

        name = meta.get("name")
        kind = meta.get("kind") or meta.get("type")
        path = meta.get("path") or meta.get("file")
        fav = {"name": name, "type": kind, "file": path}

        if self._is_favorite(name, kind, path):
            self.config.remove_favorite(fav)
            self.append_signal.emit(f"Favorito removido: {name}")
        else:
            self.config.add_favorite(fav)
            self.append_signal.emit(f"Favorito adicionado: {name}")
        self._refresh_favorites_ui()

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
            self._refresh_suggestions()
            threading.Thread(target=self._index_project, daemon=True).start()
        except Exception as e:
            self.append_signal.emit(f"Erro ao inicializar indexador: {e}")
