from pathlib import Path
from qa import knowledge, gitnexus
from qa.config import settings


def store_path(flow_id: str) -> Path:
    return settings.knowledge_dir / "system" / f"{flow_id}.md"


def contribute(flow_id: str, body_md: str, source_symbols: list[str]) -> Path:
    path = store_path(flow_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = knowledge.KnowledgeDoc(
        path=path,
        meta={"kind": "system-map", "flow": flow_id,
              "note": "MÔ TẢ code đang làm gì — KHÔNG phải oracle",
              "source_symbols": source_symbols,
              "source_hash": gitnexus.symbol_hash(source_symbols)},
        body=body_md,
    )
    knowledge.save(doc)
    return path
