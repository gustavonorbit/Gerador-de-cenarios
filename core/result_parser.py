
"""
Result parser.

Responsibility:
 - Detect and parse lines that start with `RESULT::key=value`.
 - Provide small helpers to extract key/value pairs.
"""
from typing import Dict, Any, Optional


def parse_result_line(line: str) -> Optional[Dict[str, str]]:
    """Parse a single RESULT:: line into a dict.

    Example:
        'RESULT::paciente_id=12345' -> {'paciente_id': '12345'}
    """
    if not line.startswith("RESULT::"):
        return None
    payload = line[len("RESULT::") :].strip()
    # Support multiple key=val pairs separated by semicolon or comma in future;
    # for now handle single key=value
    if "=" in payload:
        k, v = payload.split("=", 1)
        return {k.strip(): v.strip()}
    else:
        return {"result": payload}

