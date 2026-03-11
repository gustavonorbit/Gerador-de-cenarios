"""
Argument parser for Robot runner files.

Responsibility:
 - Read a .robot file and extract variable names used as `${name}`.
 - Return a list of unique argument names (without `${}`).

Notes:
 - This is a simple parser using regex; it doesn't fully parse Robot syntax but
   covers common cases such as `*** Variables ***` definitions and `[Arguments]`.
"""
from pathlib import Path
from typing import List
import re


VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def extract_arguments_from_file(file_path: str) -> List[str]:
    p = Path(file_path)
    if not p.exists():
        return []

    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return []

    # Find all ${var} occurrences
    found = VAR_PATTERN.findall(text)
    # Return unique preserving order
    seen = set()
    result = []
    for v in found:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result
