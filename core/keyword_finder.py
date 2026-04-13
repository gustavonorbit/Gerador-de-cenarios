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
                        self._keyword_to_files.setdefault(name, set()).add(str(path))
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
                        self._test_to_files.setdefault(name, set()).add(str(path))
                continue

    def search(self, query: str, limit: int = 50) -> List[Tuple[str, str]]:
        """Return list of (name, kind) matching query (case-insensitive substring).

        kind is 'keyword' or 'test'.
        """
        if not query:
            return []
        q = query.lower()
        results: List[Tuple[str, str]] = []
        for k in self._keyword_to_files.keys():
            if q in k.lower():
                results.append((k, "keyword"))
        for t in self._test_to_files.keys():
            if q in t.lower():
                results.append((t, "test"))
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

