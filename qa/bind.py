import json
from dataclasses import dataclass
from datetime import datetime, timezone
from qa import llm, gitnexus
from qa.design import Case

_TCS_KEYS = ["id", "screen", "pri", "result", "title", "pre", "steps",
             "expect", "actual", "note", "before", "after"]


@dataclass
class Seam:
    type: str            # "ui" | "headless"
    create: str
    observe: str
    source_symbols: list[str]


def to_tcs(cases: list[Case]) -> list[dict]:
    rows = []
    for c in cases:
        rows.append({
            "id": c.id, "screen": c.screen, "pri": c.pri, "result": "未実施",
            "title": c.title, "pre": c.pre, "steps": c.steps, "expect": c.expect,
            "actual": "未実施", "note": "", "before": None, "after": None,
        })
    return rows


def build_prompt(case: Case, facts: str) -> str:
    return f"""Bạn là QA senior HIỂU hệ thống. Dưới đây là 1 test case (đã chốt kỳ vọng) và FACTS từ GitNexus.
CHỈ xác định *chỗ chạm hệ thống* để chạy được case — TUYỆT ĐỐI KHÔNG sửa/diễn giải lại `expect`.

Trả về MỘT khối ```json: {{type, create, observe, source_symbols}}
- type: "ui" nếu thao tác qua màn hình; "headless" nếu qua API/DB.
- create: chỗ/bước tạo dữ liệu (app/màn hoặc API).
- observe: chỗ quan sát kết quả (màn hoặc bảng DB/endpoint).
- source_symbols: các symbol code liên quan (để truy vết), dạng "repo:path#sym".

## CASE
title: {case.title}
steps: {case.steps}
expect: {case.expect}

## FACTS (GitNexus)
{facts}
"""


def parse_seam(raw: str) -> Seam:
    data = json.loads(llm.extract_block(raw, "json"))
    return Seam(type=str(data.get("type", "ui")), create=str(data.get("create", "")),
                observe=str(data.get("observe", "")),
                source_symbols=list(data.get("source_symbols", [])))


def bind_seams(cases: list[Case], flow_id: str) -> tuple[list[dict], dict]:
    tcs = to_tcs(cases)
    frozen = {c.id: (c.title, c.expect, c.steps) for c in cases}
    trace = {"flow": flow_id,
             "generated_at": datetime.now(timezone.utc).isoformat(),
             "cases": {}}
    by_id = {c.id: c for c in cases}
    for row in tcs:
        c = by_id[row["id"]]
        facts = gitnexus.query("@threease", f"{c.title} {c.steps}")
        seam = parse_seam(llm.call(build_prompt(c, facts)))
        # ranh giới thép 1b: KHÔNG được đổi expect/title/steps
        assert (row["title"], row["expect"], row["steps"]) == frozen[row["id"]], \
            f"bind vi phạm: đã sửa expect của {row['id']}"
        row["note"] = f"[seam:{seam.type}] tạo: {seam.create} · xem: {seam.observe}"
        trace["cases"][c.id] = {
            "spec_section": c.spec_section,
            "seam": {"type": seam.type, "create": seam.create, "observe": seam.observe},
            "source_symbols": seam.source_symbols,
            "source_hash": gitnexus.symbol_hash(seam.source_symbols),
        }
    return tcs, trace
