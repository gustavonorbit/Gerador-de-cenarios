from typing import List, Optional
import tempfile
from pathlib import Path


def build_temp_suite(keywords: List[str], repo_root: Optional[str] = None, resource_path: Optional[str] = None) -> str:
    """Generate a temporary .robot suite from a list of keywords.

    - Supports up to 5 keywords (keeps order).
    - If `resource_path` is provided, include it as `Resource` in settings.
      If the resource file is inside `repo_root`, use a relative path.
    - Saves to a secure temporary file and returns its path.
    """
    kws = keywords[:5]

    lines = ["*** Settings ***", "Library    BuiltIn"]
    # determine resource entry
    if resource_path:
        rp = Path(resource_path)
        if repo_root:
            try:
                rel = Path(resource_path).relative_to(Path(repo_root))
                resource_entry = str(rel).replace("\\", "/")
            except Exception:
                resource_entry = str(rp)
        else:
            resource_entry = str(rp)
        lines.append(f"Resource    {resource_entry}")
    else:
        # default fallback to tests_robot/keywords.robot if exists in repo
        lines.append("Resource    tests_robot/keywords.robot")

    lines.append("")
    lines.extend(["*** Test Cases ***", "Executar Suite Montada"])
    for k in kws:
        # indent a keyword line with 4 spaces (Robot indentation)
        lines.append(f"    {k}")

    content = "\n".join(lines) + "\n"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".robot", prefix="suite_", mode="w", encoding="utf-8")
    try:
        tmp.write(content)
        tmp.flush()
        return tmp.name
    finally:
        tmp.close()
