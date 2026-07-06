import hashlib
import re
import subprocess
from qa.config import settings

def extract_block(text: str, lang: str) -> str:
    pattern = re.compile(rf"```{lang}\s*\n(.*?)```", re.DOTALL)
    m = pattern.search(text)
    if m:
        return m.group(1).rstrip("\n").strip("\n")
    return text.strip()

def call(prompt: str, *, cache_key: str | None = None) -> str:
    settings.cache_dir.mkdir(exist_ok=True)
    key = cache_key or hashlib.sha256(prompt.encode()).hexdigest()[:16]
    cache_file = settings.cache_dir / f"{key}.txt"
    if cache_file.exists():
        return cache_file.read_text()
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {result.stderr[:500]}")
    out = result.stdout.strip()
    cache_file.write_text(out)
    return out
