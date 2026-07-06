from pathlib import Path
from qa import llm, knowledge
from qa.config import settings


def build_prompt(doc_body: str) -> str:
    return f"""Bạn là QA automation engineer. Dưới đây là TÀI LIỆU NGHIỆP VỤ ĐÃ ĐƯỢC DUYỆT
cho luồng sync customer (backend→ticket). CHỈ dựa vào tài liệu này, KHÔNG suy đoán từ code.

Viết một file pytest kiểm chứng luồng. Dùng ĐÚNG helper có sẵn:

    from qa.runner import create_customer_via_rails, wait_for_ticket_customer, flush_outbox

- Tạo customer: `code = create_customer_via_rails(name="QA-<unique>")`  → trả customer_code.
- Kiểm sync: `found = wait_for_ticket_customer(code, timeout=15)`; nếu False thì `flush_outbox()`
  rồi `wait_for_ticket_customer(code, timeout=15)` lại (xử lý nhánh outbox — QUAN TRỌNG chống flaky).
- assert cuối: customer phải xuất hiện bên ticket.

Chỉ trả về code Python trong một khối ```python. Tên test: test_customer_syncs_to_ticket.

## TÀI LIỆU ĐÃ DUYỆT
{doc_body}
"""


def generate(doc_path: Path) -> Path:
    if not knowledge.is_approved(doc_path):
        raise ValueError(f"doc not approved: {doc_path}")
    doc = knowledge.load(doc_path)
    prompt = build_prompt(doc.body)
    raw = llm.call(prompt, cache_key="testgen_customer_sync")
    code = llm.extract_block(raw, "python")
    out = settings.generated_dir / "test_customer_sync.py"
    settings.generated_dir.mkdir(exist_ok=True)
    out.write_text(code)
    return out
