from pathlib import Path
from qa import llm, gitnexus, knowledge
from qa.config import settings

SOURCE_SYMBOLS = [
    "backend:app/models/concerns/threease_ticket_syncable.rb",
    "backend:app/jobs/threease_ticket_sync_job.rb#perform",
    "ticket:admin_api/data_sync/handlers.py#sync_data",
]

CODE_FILES = {
    "backend/app/models/concerns/threease_ticket_syncable.rb":
        settings.threesides_root / "threease_backend/app/models/concerns/threease_ticket_syncable.rb",
    "backend/app/jobs/threease_ticket_sync_job.rb":
        settings.threesides_root / "threease_backend/app/jobs/threease_ticket_sync_job.rb",
    "ticket/admin_api/data_sync/handlers.py":
        settings.threesides_root / "threease_ticket/admin_api/data_sync/handlers.py",
}

def build_prompt(facts: str, code_snippets: dict[str, str]) -> str:
    code_block = "\n\n".join(f"### {name}\n```\n{code}\n```" for name, code in code_snippets.items())
    return f"""Bạn là senior QA/BA. Đọc FACTS (từ GitNexus) và CODE dưới đây rồi viết một
tài liệu nghiệp vụ (living doc) cho luồng "sync customer từ backend (Rails) sang ticket (Django)".

Tài liệu phải là Markdown, mô tả (bằng tiếng Việt):
- Business Flow: các bước, nêu rõ nhánh direct-webhook và nhánh outbox-fallback.
- Business Rules: điều kiện sync, khi nào rơi outbox, retry.
- State Machine: trạng thái outbox event (pending→sent→failed).
- Cách kiểm chứng (assert) rằng customer ĐÃ sync sang ticket.

QUAN TRỌNG: đây là bản NHÁP (draft) để con người duyệt — mô tả code ĐANG làm gì,
không phán đúng-sai. Chỉ trả về Markdown trong một khối ```markdown.

## FACTS (GitNexus)
{facts}

## CODE
{code_block}
"""

def extract() -> Path:
    facts = gitnexus.query("@threease", "customer sync backend to ticket webhook outbox")
    snippets = {}
    for name, path in CODE_FILES.items():
        snippets[name] = Path(path).read_text() if Path(path).exists() else "(missing)"
    prompt = build_prompt(facts, snippets)
    raw = llm.call(prompt, cache_key="extract_customer_sync")
    body = llm.extract_block(raw, "markdown")
    src_hash = gitnexus.symbol_hash(list(snippets.values()))
    doc = knowledge.KnowledgeDoc(
        path=settings.knowledge_dir / "customer-sync.md",
        meta={
            "id": "customer-sync",
            "status": "draft",
            "spans_repos": ["backend", "ticket"],
            "source_symbols": SOURCE_SYMBOLS,
            "source_hash": src_hash,
        },
        body=body,
    )
    settings.knowledge_dir.mkdir(exist_ok=True)
    knowledge.save(doc)
    return doc.path
