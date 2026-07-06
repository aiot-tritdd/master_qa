from qa.extractor import build_prompt

def test_prompt_includes_facts_and_code():
    p = build_prompt("FACTS_HERE", {"foo.rb": "def foo; end"})
    assert "FACTS_HERE" in p
    assert "foo.rb" in p
    assert "def foo" in p
    assert "draft" in p.lower()  # instructs LLM about status
