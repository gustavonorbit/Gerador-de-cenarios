from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import re


class KeywordFinder:
    """Index and search Robot Framework keywords and tests inside a project root.

    - Indexes `*.robot` and `*.resource` files.
    - Produces maps for `keywords` and `tests` (each -> set(files)).
    - Provides unified search returning (name, kind) where kind is 'keyword' or 'test'.
    """

    DEFAULT_IGNORE = {".git", "venv", "__pycache__", "node_modules", "dist", "build", ".idea", ".vscode"}
    DATABASE_SCOPES = ("SQL", "SAP", "ORACLE")
    KNOWN_MODULES = ("CADGF", "CONSULT", "ASSIST", "ATENDE", "AGENDA", "LAB", "OCUP")

    def __init__(self, project_root: Optional[Path] = None, ignore: Optional[Set[str]] = None):
        if project_root is None:
            # default not desirable for this new architecture — require explicit root when possible
            self.project_root = Path(__file__).resolve().parent.parent
        else:
            self.project_root = Path(project_root).resolve()

        self.ignore = set(ignore) if ignore is not None else set(self.DEFAULT_IGNORE)

        # index structures
        self._keyword_to_files: Dict[str, Set[str]] = {}
        self._test_to_files: Dict[str, Set[str]] = {}
        self._items: List[Dict[str, str]] = []
        self._seen_items: Set[Tuple[str, str, str]] = set()

    def _is_ignored(self, path: Path) -> bool:
        for part in path.parts:
            if part in self.ignore:
                return True
        return False

    def index(self) -> Tuple[int, int]:
        """Index project files.

        Returns: (num_keywords, num_tests)
        """
        self._keyword_to_files.clear()
        self._test_to_files.clear()
        self._items.clear()
        self._seen_items.clear()

        patterns = ("*.robot", "*.resource")
        for pattern in patterns:
            for p in sorted(self.project_root.rglob(pattern)):
                if self._is_ignored(p):
                    continue
                try:
                    self._index_file(p)
                except Exception:
                    continue

        return len(self._keyword_to_files), len(self._test_to_files)

    def _index_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8", errors="ignore")
        relative_file = self._relative_file(path)
        module = self._detect_module(relative_file)
        database_scope = self._detect_database_scope(relative_file)

        in_keywords = False
        in_tests = False
        for raw in text.splitlines():
            line = raw.rstrip("\n\r")
            stripped = line.strip()
            low = stripped.lower()

            # section header handling
            if low.startswith("***") and low.endswith("***"):
                in_keywords = "keywords" in low
                in_tests = "test cases" in low or "tests" in low
                continue

            if in_keywords:
                if not stripped:
                    continue
                if line and (not line[0].isspace()):
                    if stripped.startswith("["):
                        continue
                    name = re.split(r"\s{2,}", stripped)[0]
                    name = re.sub(r"\s+#.*$", "", name).strip()
                    if name:
                        self._add_item(name, "keyword", path, relative_file, module, database_scope)
                continue

            if in_tests:
                if not stripped:
                    continue
                # test cases lines usually start at column 0
                if line and (not line[0].isspace()):
                    # skip settings-like lines
                    if stripped.startswith("["):
                        continue
                    name = re.split(r"\s{2,}", stripped)[0]
                    name = re.sub(r"\s+#.*$", "", name).strip()
                    if name:
                        self._add_item(name, "test", path, relative_file, module, database_scope)
                continue

    def _relative_file(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.project_root))
        except Exception:
            return str(path)

    def _detect_database_scope(self, relative_file: str) -> str:
        path_upper = relative_file.upper()
        for database in self.DATABASE_SCOPES:
            if database in path_upper:
                return database
        return "Comum"

    def _detect_module(self, relative_file: str) -> str:
        parts_upper = {part.upper() for part in Path(relative_file).parts}
        for module in self.KNOWN_MODULES:
            if module in parts_upper:
                return module
        return "Geral"

    def _add_item(
        self,
        name: str,
        kind: str,
        path: Path,
        relative_file: str,
        module: str,
        database_scope: str,
    ) -> None:
        file_path = str(path)
        if kind == "keyword":
            self._keyword_to_files.setdefault(name, set()).add(file_path)
        else:
            self._test_to_files.setdefault(name, set()).add(file_path)

        key = (name, kind, file_path)
        if key in self._seen_items:
            return
        self._seen_items.add(key)
        self._items.append({
            "name": name,
            "kind": kind,
            "type": kind,
            "path": file_path,
            "file": file_path,
            "relative_file": relative_file,
            "module": module,
            "database_scope": database_scope,
        })

    def all_items(self) -> List[Dict[str, str]]:
        return [dict(item) for item in self._items]

    def search_items(
        self,
        query: str = "",
        limit: Optional[int] = None,
        database_scope: Optional[str] = None,
        module: Optional[str] = None,
        kind_filter: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        q = (query or "").strip().lower()
        selected_database = (database_scope or "").strip().upper()
        selected_module = (module or "").strip().upper()
        selected_kind = (kind_filter or "").strip().lower()

        results: List[Dict[str, str]] = []
        for item in self._items:
            if q and q not in item.get("name", "").lower():
                continue

            if selected_database:
                item_database = item.get("database_scope", "Comum").upper()
                if item_database not in (selected_database, "COMUM"):
                    continue

            if selected_module and item.get("module", "").upper() != selected_module:
                continue

            if selected_kind and item.get("kind") != selected_kind:
                continue

            results.append(dict(item))

        results.sort(key=self._item_sort_key)
        if limit is not None:
            return results[:limit]
        return results

    def modules_for(
        self,
        database_scope: Optional[str] = None,
        kind_filter: Optional[str] = None,
    ) -> List[str]:
        items = self.search_items(
            "",
            limit=None,
            database_scope=database_scope,
            kind_filter=kind_filter,
        )
        modules = {item.get("module") or "Geral" for item in items}
        return sorted(modules, key=self._module_sort_key)

    def _item_sort_key(self, item: Dict[str, str]) -> Tuple[int, int, str, str]:
        return (
            self._module_sort_key(item.get("module") or "Geral"),
            0 if item.get("kind") == "keyword" else 1,
            item.get("name", "").lower(),
            item.get("relative_file", "").lower(),
        )

    def _module_sort_key(self, module: str) -> int:
        try:
            return self.KNOWN_MODULES.index(module)
        except ValueError:
            return len(self.KNOWN_MODULES)

    def search(self, query: str, limit: int = 50) -> List[Tuple[str, str]]:
        """Return list of (name, kind) matching query (case-insensitive substring).

        kind is 'keyword' or 'test'.
        """
        q = query or ""
        results: List[Tuple[str, str]] = []
        seen: Set[Tuple[str, str]] = set()
        for item in self.search_items(q, limit=None):
            key = (item.get("name", ""), item.get("kind", ""))
            if key in seen:
                continue
            seen.add(key)
            results.append(key)
        results.sort(key=lambda s: (s[1], s[0].lower()))
        return results[:limit]

    def get_files_for(self, name: str, kind: str) -> List[str]:
        if kind == "keyword":
            vals = self._keyword_to_files.get(name)
        else:
            vals = self._test_to_files.get(name)
        if not vals:
            return []
        return sorted(vals)

    def get_keyword_arguments(self, name: str, file_path: Optional[str] = None) -> List[str]:
        """Locate the keyword definition in indexed files and extract argument names.

        Returns argument names in order, without ${}.
        """
        files = self.get_files_for(name, "keyword")
        if file_path and file_path in files:
            files = [file_path] + [f for f in files if f != file_path]
        if not files:
            return []

        for f in files:
            try:
                text = Path(f).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            in_keywords = False
            lines = text.splitlines()
            for idx, raw in enumerate(lines):
                line = raw.rstrip("\n\r")
                stripped = line.strip()
                low = stripped.lower()

                # section header handling
                if low.startswith("***") and low.endswith("***"):
                    in_keywords = "keywords" in low
                    continue

                if not in_keywords:
                    continue

                # keyword definition lines usually start at column 0 (no indent)
                if line and (not line[0].isspace()):
                    # get the keyword name on this line
                    if stripped.startswith("["):
                        continue
                    name_on_line = re.split(r"\s{2,}", stripped)[0]
                    name_on_line = re.sub(r"\s+#.*$", "", name_on_line).strip()
                    if name_on_line != name:
                        continue
                    # found keyword definition; scan following indented block for [Arguments]
                    arg_names: List[str] = []
                    j = idx + 1
                    while j < len(lines):
                        next_line = lines[j]
                        if not next_line.strip():
                            j += 1
                            continue
                        # section header or new top-level keyword stops the block
                        if next_line.strip().lower().startswith("***"):
                            break
                        if not next_line[0].isspace():
                            # next top-level keyword or test case
                            break

                        s = next_line.strip()
                        low_s = s.lower()
                        if low_s.startswith("[arguments]"):
                            # extract all ${...} occurrences and strip ${}
                            found = re.findall(r"\$\{([^}]+)\}", s)
                            # fallback: if no ${}, split remaining by two+ spaces or tabs
                            if not found:
                                rest = s[len("[Arguments]"):].strip() if s.lower().startswith("[arguments]") else s
                                parts = re.split(r"\s{2,}|\t+", rest)
                                for p in parts:
                                    p = p.strip()
                                    if not p:
                                        continue
                                    # remove possible ${}
                                    m = re.match(r"\$\{([^}]+)\}", p)
                                    if m:
                                        arg_names.append(m.group(1))
                                    else:
                                        arg_names.append(p.lstrip("$").strip("{}"))
                            else:
                                arg_names.extend(found)
                            # return first occurrence
                            return [a for a in arg_names]
                        j += 1
        return []
