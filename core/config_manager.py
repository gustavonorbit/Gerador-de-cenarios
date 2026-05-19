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
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    # Note: repository/base resource paths are no longer managed here.
    # This class keeps a generic config file for other unrelated preferences.

    # --- automation root persistence ---
    def get_automation_root_path(self) -> str | None:
        cfg = self.load()
        val = cfg.get("automation_root_path")
        if val:
            return str(val)
        return None

    def set_automation_root_path(self, path: str | None) -> None:
        cfg = self.load()
        if path is None:
            cfg.pop("automation_root_path", None)
        else:
            cfg["automation_root_path"] = str(path)
        self._config = cfg
        self.save()

    # --- favorites persistence ---
    def get_favorites(self) -> list:
        cfg = self.load()
        favs = cfg.get("favorites")
        if not isinstance(favs, list):
            return []
        return favs

    def set_favorites(self, favorites: list) -> None:
        cfg = self.load()
        cfg["favorites"] = favorites
        self._config = cfg
        self.save()

    def add_favorite(self, fav: dict) -> None:
        favs = self.get_favorites()
        # avoid duplicates by tuple (name,type,file)
        key = (fav.get("name"), fav.get("type"), fav.get("file"))
        for f in favs:
            if (f.get("name"), f.get("type"), f.get("file")) == key:
                return
        favs.append({"name": fav.get("name"), "type": fav.get("type"), "file": fav.get("file")})
        self.set_favorites(favs)

    def remove_favorite(self, fav: dict) -> None:
        favs = self.get_favorites()
        key = (fav.get("name"), fav.get("type"), fav.get("file"))
        new = [f for f in favs if (f.get("name"), f.get("type"), f.get("file")) != key]
        if len(new) != len(favs):
            self.set_favorites(new)

    # --- saved scenarios persistence ---
    def get_saved_scenarios(self) -> list:
        cfg = self.load()
        sc = cfg.get("saved_scenarios")
        if not isinstance(sc, list):
            return []
        return sc

    def set_saved_scenarios(self, scenarios: list) -> None:
        cfg = self.load()
        cfg["saved_scenarios"] = scenarios
        self._config = cfg
        self.save()

    def add_or_update_scenario(self, scenario: dict) -> None:
        """Add or update scenario by name."""
        if not scenario or not isinstance(scenario, dict):
            return
        name = scenario.get("name")
        if not name:
            return
        scs = self.get_saved_scenarios()
        for i, s in enumerate(scs):
            if s.get("name") == name:
                scs[i] = scenario
                self.set_saved_scenarios(scs)
                return
        scs.append(scenario)
        self.set_saved_scenarios(scs)

    def remove_scenario(self, name: str) -> None:
        if not name:
            return
        scs = self.get_saved_scenarios()
        new = [s for s in scs if s.get("name") != name]
        if len(new) != len(scs):
            self.set_saved_scenarios(new)
