from pathlib import Path
import json


class ConfigManager:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.config_path = self.project_root / "config.json"
        self._config = None

    def load(self) -> dict:
        if self._config is not None:
            return self._config
        if not self.config_path.exists():
            self._config = {}
            return self._config
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except Exception:
            self._config = {}
        return self._config

    def save(self) -> None:
        if self._config is None:
            self._config = {}
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # Note: repository/base resource paths are no longer managed here.
    # This class keeps a generic config file for other unrelated preferences.
