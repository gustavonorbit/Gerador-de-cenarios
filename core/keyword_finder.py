from pathlib import Path
from typing import Dict, List, Set, Optional
import re


class KeywordFinder:
    """Index and search Robot Framework keywords inside a project root.

    Behavior:
    - Detect project root automatically if not provided.
    - Index files with extensions .robot and .resource, ignoring common folders.
    - Provide search(query) to get suggestion list and get_files_for_keyword(keyword).
    """

    DEFAULT_IGNORE = {".git", "venv", "__pycache__", "node_modules", "dist", "build", ".idea", ".vscode"}

    def __init__(self, project_root: Optional[Path] = None, ignore: Optional[Set[str]] = None):
        if project_root is None:
            # assume package layout: core/ -> project root is two levels up from this file
            self.project_root = Path(__file__).resolve().parent.parent
        else:
            self.project_root = Path(project_root).resolve()
        self.ignore = set(ignore) if ignore is not None else set(self.DEFAULT_IGNORE)

        # index structures
        self._keyword_to_files: Dict[str, Set[str]] = {}

    def _is_ignored(self, path: Path) -> bool:
        for part in path.parts:
            if part in self.ignore:
                return True
        return False

    def index(self) -> int:
        """Index project files and return number of distinct keywords found."""
        self._keyword_to_files.clear()
        patterns = ("*.robot", "*.resource")
        for pattern in patterns:
            for p in sorted(self.project_root.rglob(pattern)):
                if self._is_ignored(p):
                    continue
                try:
                    self._index_file(p)
                except Exception:
                    # skip unreadable files but continue indexing
                    continue

        return len(self._keyword_to_files)

    def _index_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8", errors="ignore")

        in_keywords = False
        for raw in text.splitlines():
            line = raw.rstrip("\n\r")
            stripped = line.strip()
            low = stripped.lower()

            # section header handling
            if low.startswith("***") and low.endswith("***"):
                # detect keywords section start
                if "keywords" in low:
                    in_keywords = True
                else:
                    in_keywords = False
                continue

            if not in_keywords:
                continue

            # a keyword definition in a Keywords section is typically a non-empty
            # line that does not start with whitespace (or with '[' which is a setting)
            if not stripped:
                continue
            # Robot keywords normally start at column 0 (no indentation)
            if line and (not line[0].isspace()):
                # Filter out possible settings-like lines
                if stripped.startswith("["):
                    continue
                # take the token until two or more spaces (arguments separator) or full line
                # also trim trailing inline comments
                name = re.split(r"\s{2,}", stripped)[0]
                name = re.sub(r"\s+#.*$", "", name).strip()
                if name:
                    key = name
                    lst = self._keyword_to_files.setdefault(key, set())
                    lst.add(str(path))

    def search(self, query: str, limit: int = 50) -> List[str]:
        """Return matching keyword names (case-insensitive substring)."""
        if not query:
            return []
        q = query.lower()
        results = [k for k in self._keyword_to_files.keys() if q in k.lower()]
        results.sort(key=lambda s: s.lower())
        return results[:limit]

    def get_files_for_keyword(self, keyword: str) -> List[str]:
        vals = self._keyword_to_files.get(keyword)
        if not vals:
            return []
        return sorted(vals)
