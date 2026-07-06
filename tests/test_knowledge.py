from pathlib import Path
from qa.knowledge import load, save, is_approved, KnowledgeDoc

SAMPLE = """---
id: demo
status: draft
source_symbols:
  - backend:foo.rb
---
# Body
hello
"""

def test_roundtrip(tmp_path):
    p = tmp_path / "demo.md"
    p.write_text(SAMPLE)
    doc = load(p)
    assert doc.meta["id"] == "demo"
    assert doc.meta["status"] == "draft"
    assert "hello" in doc.body
    assert not is_approved(p)

def test_save_changes_status(tmp_path):
    p = tmp_path / "demo.md"
    p.write_text(SAMPLE)
    doc = load(p)
    doc.meta["status"] = "approved"
    save(doc)
    assert is_approved(p)
