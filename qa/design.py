import json
import re
from dataclasses import dataclass
from qa import llm  # 1a MÙ CODE: chỉ llm; không import graph engine, không đọc repo (ranh giới thép)


@dataclass
class Case:
    id: str
    screen: str
    pri: str
    title: str
    pre: str
    steps: str
    expect: str
    spec_section: str


def extract_sections(spec_md: str) -> list[str]:
    secs: list[str] = []
    for line in spec_md.splitlines():
        s = line.strip()
        if re.match(r"^#{2,4}\s+\S", s) or re.match(r"^[①②③④⑤⑥⑦⑧⑨]", s) or "【" in s:
            secs.append(re.sub(r"^#{2,4}\s+", "", s))
    return secs


def build_prompt(spec_md: str) -> str:
    return f"""Bạn là QA senior. CHỈ dựa trên TÀI LIỆU SPEC dưới đây (nghiệp vụ khách đã chốt),
thiết kế bộ test case. TUYỆT ĐỐI không suy đoán từ code — bạn KHÔNG có code.

Mỗi case: happy path / biến thể quyền-điều kiện / boundary / regression / negative.
`expect` phải là hành vi ĐÚNG theo spec (kể cả thông báo nguyên văn nếu spec ghi), KHÔNG mô tả "hệ thống đang làm gì".
`spec_section` = mục trong spec mà case này truy về (vd "①Company", "【A】").
`steps`/`pre` viết bằng NGÔN NGỮ NGHIỆP VỤ (chưa cần biết URL/màn hình cụ thể).

Chỉ trả về MỘT khối ```json là mảng object, mỗi object khoá:
id (TC-01…), screen, pri (High|Medium|Low), title, pre, steps, expect, spec_section.

## SPEC
{spec_md}
"""


def parse_cases(raw: str) -> list[Case]:
    block = llm.extract_block(raw, "json")
    data = json.loads(block)
    return [Case(**{k: str(item.get(k, "")) for k in Case.__annotations__}) for item in data]


def build_cases(spec_md: str) -> list[Case]:
    raw = llm.call(build_prompt(spec_md))
    return parse_cases(raw)
