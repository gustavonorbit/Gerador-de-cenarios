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

    def get_repository_path(self) -> str | None:
        cfg = self.load()
        return cfg.get("repository_path")

    def set_base_resource_path(self, path: str) -> None:
        cfg = self.load()
        cfg["base_resource_path"] = path
        self._config = cfg
        self.save()

    def get_base_resource_path(self) -> str | None:
        cfg = self.load()
        return cfg.get("base_resource_path")

    def set_repository_path(self, path: str) -> None:
        cfg = self.load()
        cfg["repository_path"] = path
        self._config = cfg
        self.save()
