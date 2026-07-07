import subprocess
import time
from qa.config import settings


def _compose(*args: str) -> list[str]:
    return ["docker", "compose", "-f", str(settings.compose_file), *args]


# NOTE: attributes below are the discovered minimal valid set from Task 7 Step 1
# discovery (run 2026-07-06 against the live threease_backend container).
# branch_id=2 is a valid existing branch (verified via Therapists::Customer.find(174)).
CREATE_SNIPPET = '''
code = "{code}"
c = Therapists::Customer.new(name: "{name}", customer_code: code, branch_id: 2)
c.save!(validate: false)
puts code
'''


def create_customer_via_rails(name: str) -> str:
    code = "qa" + str(int(time.time()))
    script = CREATE_SNIPPET.format(code=code, name=name)
    result = subprocess.run(
        _compose("exec", "-T", settings.backend_service, "bundle", "exec", "rails", "runner", script),
        capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(f"rails create failed: {result.stderr[-800:]}")
    return code


def wait_for_ticket_customer(customer_code: str, timeout: int = 15) -> bool:
    deadline = time.time() + timeout
    sql = f"SELECT count(*) FROM th_customer WHERE customer_code = '{customer_code}';"
    while time.time() < deadline:
        result = subprocess.run(
            _compose("exec", "-T", settings.ticket_db_service,
                     "psql", "-U", "threease_dev", "-d", "threease_ticket", "-tAc", sql),
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip().isdigit() and int(result.stdout.strip()) > 0:
            return True
        time.sleep(2)
    return False


def flush_outbox() -> None:
    subprocess.run(
        _compose("exec", "-T", settings.backend_service, "bundle", "exec", "rake", "threease_ticket:flush_outbox"),
        capture_output=True, text=True, timeout=180,
    )


def run_generated() -> dict:
    result = subprocess.run(
        ["python", "-m", "pytest", str(settings.generated_dir), "-v"],
        cwd=settings.qa_root, capture_output=True, text=True, timeout=300,
    )
    return {"passed": result.returncode == 0, "output": result.stdout + result.stderr}
