from typing import List, Optional
import tempfile
from pathlib import Path


def _to_resource_entry(repo_root: Path, path_str: str) -> str:
    p = Path(path_str)
    if not p.is_absolute():
        # assume relative path already
        return str(p).replace("\\", "/")
    try:
        rel = p.relative_to(repo_root)
        return str(rel).replace("\\", "/")
    except Exception:
        return str(p)


def build_temp_suite(keywords: List[str], repo_root: Path, resource_paths: Optional[List[str]] = None) -> str:
    """Generate a temporary .robot suite from a list of keywords.

    - Uses the project `repo_root` as base for Resource relative paths.
    - Accepts `resource_paths` as a list of files that should be included as Resource entries.
    - If no resources are provided, falls back to `tests_robot/keywords.robot`.
    - Supports up to 5 keywords (keeps order).
    """
    kws = keywords[:5]

    lines = ["*** Settings ***", "Library    BuiltIn"]

    if resource_paths:
        for rp in resource_paths:
            try:
                entry = _to_resource_entry(Path(repo_root), rp)
                lines.append(f"Resource    {entry}")
            except Exception:
                # best-effort include
                lines.append(f"Resource    {rp}")
    else:
        # default fallback
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
