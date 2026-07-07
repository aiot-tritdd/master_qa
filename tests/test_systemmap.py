import types
import qa.systemmap as sm


def test_contribute_writes_doc_with_provenance(tmp_path, monkeypatch):
    # settings là frozen dataclass → thay cả reference bằng fake, không mutate instance
    monkeypatch.setattr(sm, "settings", types.SimpleNamespace(knowledge_dir=tmp_path))
    p = sm.contribute("10.4-customer", "# Flow\nBackend -> Ticket", ["backend:x", "ticket:y"])
    doc = sm.knowledge.load(p)
    assert doc.meta["kind"] == "system-map"
    assert doc.meta["flow"] == "10.4-customer"
    assert doc.meta["source_symbols"] == ["backend:x", "ticket:y"]
    assert doc.meta["source_hash"]           # có hash provenance
    assert "Backend -> Ticket" in doc.body
