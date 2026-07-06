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

def test_roundtrip_body_with_dashes(tmp_path):
    from qa.knowledge import load, save
    text = "---\nid: test\nstatus: draft\n---\n\n# Code\n---\nafter\n"
    p = tmp_path / "test.md"
    p.write_text(text)
    doc = load(p)
    assert "---" in doc.body
    doc.meta["status"] = "approved"
    save(doc)
    doc2 = load(p)
    assert doc2.body == doc.body       # embedded dashes preserved
    assert doc2.meta["status"] == "approved"
