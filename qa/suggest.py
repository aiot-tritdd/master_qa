import json
from pathlib import Path
from qa.specmd import ingest
from qa.design import build_cases, extract_sections
from qa.bind import bind_seams


def coverage(cases, sections) -> dict:
    counts = {s: 0 for s in sections}
    for c in cases:
        counts[c.spec_section] = counts.get(c.spec_section, 0) + 1
    return counts


def suggest(folder: Path) -> dict:
    folder = Path(folder)
    if (folder / "specs.html").exists() and not (folder / "specs.md").exists():
        ingest(folder)
    spec_md = (folder / "specs.md").read_text(encoding="utf-8")
    cases = build_cases(spec_md)
    tcs, trace = bind_seams(cases, flow_id=folder.name)
    payload = {
        "meta": {"project": "Threesides Maintenance", "module": folder.name,
                 "issue": "", "tester": "QA-Server (brain)", "date": "", "env": "Dev"},
        "shots_dir": "shots", "tcs": tcs,
    }
    tcs_path = folder / "tcs.json"
    trace_path = folder / "trace.json"
    tcs_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"tcs": str(tcs_path), "trace": str(trace_path),
            "coverage": coverage(cases, extract_sections(spec_md))}
