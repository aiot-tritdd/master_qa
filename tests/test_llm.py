from qa.llm import extract_block, call
from qa import llm
from qa.config import settings

def test_extract_fenced_markdown():
    text = "blah\n```markdown\n# Title\nbody\n```\ntrailing"
    assert extract_block(text, "markdown") == "# Title\nbody"

def test_extract_missing_fence_returns_stripped():
    assert extract_block("  raw text  ", "python") == "raw text"

def test_extract_first_of_multiple():
    text = "```python\na=1\n```\n```python\nb=2\n```"
    assert extract_block(text, "python") == "a=1"

def test_call_cache_key_varies_with_prompt(tmp_path, monkeypatch):
    """Different prompts must not share a cache entry."""
    calls = []

    class MockResult:
        returncode = 0
        stdout = "OUT"
        stderr = ""

    def mock_run(*args, **kwargs):
        calls.append(args)
        return MockResult()

    # Create a mock settings object with cache_dir set to tmp_path
    class MockSettings:
        cache_dir = tmp_path

    monkeypatch.setattr(llm.subprocess, "run", mock_run)
    monkeypatch.setattr(llm, "settings", MockSettings())

    # Call with two different prompts
    call("prompt ONE")
    call("prompt TWO")
    assert len(calls) == 2, "Different prompts should invoke subprocess twice"

    # Call first prompt again - should hit cache, no new subprocess call
    call("prompt ONE")
    assert len(calls) == 2, "Repeated prompt should hit cache, not invoke subprocess again"
