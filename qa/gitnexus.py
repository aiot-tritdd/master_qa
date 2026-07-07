import hashlib
import subprocess
from qa.config import settings

def run(args: list[str]) -> str:
    result = subprocess.run(
        ["gitnexus", *args],
        cwd=settings.threesides_root,
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gitnexus {args} failed: {result.stderr[:500]}")
    return result.stdout

def query(repo: str, q: str) -> str:
    return run(["query", "--repo", repo, q])

def impact(repo: str, target: str, direction: str = "upstream") -> str:
    return run(["impact", "--repo", repo, "--target", target, "--direction", direction])

def symbol_hash(texts: list[str]) -> str:
    h = hashlib.sha256()
    for t in texts:
        h.update(t.encode())
    return h.hexdigest()[:16]
