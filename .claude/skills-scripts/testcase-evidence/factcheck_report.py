#!/usr/bin/env python3
# factcheck_report.py — soi report-source JSON (tcs.json / *.results.json / bug-he-thong.tcs.json)
# TRƯỚC khi build Excel / append sổ. Giữ tính TRUNG THỰC của chữ trong report (bê từ qa-report-humanizer,
# kindlmann MIT — phần mechanical). THUẦN observe: KHÔNG phán đúng/sai nghiệp vụ.
#
# GATE (exit != 0):
#   1) Filler / AI-tell: văn robot ("Moving forward", "the team is committed to"…) — QA thật không viết vậy.
#   2) Tally bịa: mọi "N PASS/FAIL/未実施" viết trong field summary/meta phải KHỚP số đếm THẬT trong doc.
# WARN (không gate): synonym-cycling, passive "ai làm gãy", định lượng mơ hồ (several/various/potentially).
#
# Chạy: python3 factcheck_report.py <report-source.json>

import sys
import json
import re

FILLER_RE = re.compile(
    r"it('?s)? worth noting|moving forward|in conclusion|despite (several )?challenges|"
    r"the team is (committed|aligned)|stakeholders can feel confident|underscor(es|ing)|"
    r"demonstrating significant|showcasing the team|continued vigilance|proactive testing|"
    r"mitigate potential|potential(ly)? impact|high-risk areas|continuous improvement|"
    r"enhanced test coverage|comprehensive regression|across multiple touchpoints|"
    r"trend(s|ing)? positively|high-quality release|strong collaboration|technical excellence|customer focus",
    re.I,
)
SYNONYM_RE = re.compile(r"passed successfully|completed without issues|returned positive results|executed as expected", re.I)
PASSIVE_RE = re.compile(r"an issue was identified|a defect was (discovered|identified)|was discovered that impacts", re.I)
VAGUE_RE = re.compile(r"\b(several|various|multiple|numerous|potentially)\b", re.I)
SUMMARY_PATH_RE = re.compile(r"(summary|tally|meta|overview|total)", re.I)

RESULT_TOKENS = ("PASS", "FAIL", "未実施", "SPEC-GAP")


def walk(obj, path=""):
    """yield (path, string) cho mọi leaf string trong cây JSON."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def count_results(doc):
    """Đếm verdict THẬT: screens[].result HOẶC token đầu của tcs[].result/actual."""
    counts = {}
    def bump(tok):
        if tok in RESULT_TOKENS:
            counts[tok] = counts.get(tok, 0) + 1
    if isinstance(doc, dict) and isinstance(doc.get("screens"), list):
        for s in doc["screens"]:
            if isinstance(s, dict):
                bump(s.get("result"))
    rows = doc.get("tcs") if isinstance(doc, dict) else None
    if isinstance(rows, list):
        for r in rows:
            if not isinstance(r, dict):
                continue
            tok = r.get("result")
            if tok not in RESULT_TOKENS:
                act = (r.get("actual") or "").strip()
                first = act.split()[0].rstrip(":.") if act else ""
                tok = first if first in RESULT_TOKENS else None
            bump(tok)
    return counts


def analyze(doc):
    """Trả (errors, warns, counts). errors → gate; warns → chỉ nhắc."""
    strings = list(walk(doc))
    counts = count_results(doc)
    errors, warns = [], []

    for path, s in strings:
        m = FILLER_RE.search(s)
        if m:
            errors.append(f"[filler] {path}: “…{m.group(0)}…” — văn AI, viết cụ thể cái gì gãy thay vì filler.")

    # tally-consistency: chỉ soi field summary/meta (tránh false-positive khi note cross-reference case khác)
    for path, s in strings:
        if not SUMMARY_PATH_RE.search(path):
            continue
        for tok in RESULT_TOKENS:
            for m in re.finditer(rf"(\d+)\s*{re.escape(tok)}", s):
                claimed, actual = int(m.group(1)), counts.get(tok, 0)
                if claimed != actual:
                    errors.append(f"[tally] {path}: viết {claimed} {tok} nhưng đếm thật trong doc = {actual}.")

    for path, s in strings:
        if SYNONYM_RE.search(s):
            warns.append(f"[synonym] {path}: một kết quả chỉ cần một động từ, đừng xoay 4 cách nói.")
        if PASSIVE_RE.search(s):
            warns.append(f"[passive] {path}: nói RÕ cái gì gãy (chủ động), đừng 'an issue was identified'.")
        vm = VAGUE_RE.search(s)
        if vm:
            warns.append(f"[vague:{vm.group(0)}] {path}: thay từ mơ hồ bằng con số/điều kiện cụ thể.")

    return errors, warns, counts


def main(argv):
    if len(argv) < 2:
        print("usage: factcheck_report.py <report-source.json>")
        return 2
    with open(argv[1], encoding="utf-8") as f:
        doc = json.load(f)
    errors, warns, counts = analyze(doc)
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("FAIL ", e)
    print(f"\nfactcheck: {len(errors)} lỗi (gate), {len(warns)} cảnh báo · verdict đếm được = {counts}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
