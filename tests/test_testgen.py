import pytest
from pathlib import Path
from qa.testgen import generate, build_prompt


def test_prompt_uses_doc_body():
    p = build_prompt("RULE: customer must appear in ticket")
    assert "RULE: customer must appear in ticket" in p
    assert "pytest" in p.lower()


def test_generate_refuses_unapproved(tmp_path):
    p = tmp_path / "customer-sync.md"
    p.write_text("---\nid: x\nstatus: draft\n---\n\nbody")
    with pytest.raises(ValueError, match="not approved"):
        generate(p)
