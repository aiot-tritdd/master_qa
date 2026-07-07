import json
from pathlib import Path


def affected(folder: Path, changed_symbols: list[str]) -> list[str]:
    trace = json.loads((Path(folder) / "trace.json").read_text(encoding="utf-8"))
    hits: list[str] = []
    for tc_id, info in trace.get("cases", {}).items():
        syms = info.get("source_symbols", [])
        if any(ch in s or s in ch for ch in changed_symbols for s in syms):
            hits.append(tc_id)
    return sorted(hits)
