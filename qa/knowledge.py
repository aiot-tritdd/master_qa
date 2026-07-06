import subprocess
from dataclasses import dataclass
from pathlib import Path
import yaml
from qa.config import settings

@dataclass
class KnowledgeDoc:
    path: Path
    meta: dict
    body: str

def load(path: Path) -> KnowledgeDoc:
    text = Path(path).read_text()
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
        body = body.lstrip("\n")
    else:
        meta, body = {}, text
    return KnowledgeDoc(path=Path(path), meta=meta, body=body)

def save(doc: KnowledgeDoc) -> None:
    fm = yaml.safe_dump(doc.meta, allow_unicode=True, sort_keys=False).strip()
    doc.path.write_text(f"---\n{fm}\n---\n\n{doc.body}")

def is_approved(path: Path) -> bool:
    return load(path).meta.get("status") == "approved"

def approve(path: Path) -> None:
    doc = load(path)
    doc.meta["status"] = "approved"
    save(doc)
    subprocess.run(["git", "add", str(path)], cwd=settings.qa_root, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"knowledge: approve {doc.meta.get('id', path.stem)}"],
        cwd=settings.qa_root, check=True,
    )
