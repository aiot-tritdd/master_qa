import hashlib
import re
import subprocess
import time
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
    last_err = ""
    for attempt in range(3):  # retry: claude -p đôi khi fail thoáng qua (rate-limit)
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode == 0 and result.stdout.strip():
            out = result.stdout.strip()
            cache_file.write_text(out)
            return out
        last_err = result.stderr[:500] or f"empty stdout (rc={result.returncode})"
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"claude CLI failed sau 3 lần: {last_err}")
