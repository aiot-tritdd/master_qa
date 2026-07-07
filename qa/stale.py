import json
from pathlib import Path
from qa import gitnexus


def current_hash(source_symbols: list[str]) -> str:
    facts = [gitnexus.query("@threease", s) for s in source_symbols]
    return gitnexus.symbol_hash(facts)


def check_stale(folder: Path) -> list[dict]:
    trace = json.loads((Path(folder) / "trace.json").read_text(encoding="utf-8"))
    out: list[dict] = []
    for tc_id, info in trace.get("cases", {}).items():
        old = info.get("source_hash", "")
        new = current_hash(info.get("source_symbols", []))
        out.append({"tc": tc_id, "stale": old != new, "old_hash": old, "new_hash": new})
    return out
