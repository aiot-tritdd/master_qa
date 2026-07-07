from qa import runner


def test_run_generated_reports_pass(monkeypatch):
    class R:
        returncode = 0
        stdout = "1 passed"
        stderr = ""
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: R())
    result = runner.run_generated()
    assert result["passed"] is True
    assert "passed" in result["output"]


def test_run_generated_reports_fail(monkeypatch):
    class R:
        returncode = 1
        stdout = "1 failed"
        stderr = ""
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: R())
    assert runner.run_generated()["passed"] is False
