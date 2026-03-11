"""
Runner loader.

Responsibility:
 - Discover .robot runner files under `robot/runners/` and return their names and paths.
"""
from pathlib import Path
from typing import List, Dict


class RunnerLoader:
    def __init__(self, runners_path: Path):
        self.runners_path = Path(runners_path)

    def list_runners(self) -> List[Dict[str, str]]:
        """Return a list of runners with display name and full path.

        Each item is a dict: {"name": "run_x.robot", "path": "/abs/path/..."}
        """
        runners = []
        if not self.runners_path.exists():
            return runners

        for p in sorted(self.runners_path.glob("*.robot")):
            runners.append({"name": p.name, "path": str(p)})

        return runners
