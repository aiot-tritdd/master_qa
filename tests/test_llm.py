from qa.llm import extract_block

def test_extract_fenced_markdown():
    text = "blah\n```markdown\n# Title\nbody\n```\ntrailing"
    assert extract_block(text, "markdown") == "# Title\nbody"

def test_extract_missing_fence_returns_stripped():
    assert extract_block("  raw text  ", "python") == "raw text"

def test_extract_first_of_multiple():
    text = "```python\na=1\n```\n```python\nb=2\n```"
    assert extract_block(text, "python") == "a=1"
