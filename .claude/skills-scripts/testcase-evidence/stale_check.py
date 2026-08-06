#!/usr/bin/env python3
"""stale_check.py — staleness cho knowledge/ theo source_hash. CƠ KHÍ, KHÔNG reasoning.

Ý tưởng: mỗi doc knowledge có `source_symbols` (trỏ file:symbol trong 5 repo). `source_hash` =
hash nội dung các FILE đó tại thời điểm duyệt. Code đổi → file đổi → hash đổi → doc STALE.

Usage:
  python3 stale_check.py --update    # tính + GHI source_hash vào từng doc (chạy khi grow/duyệt xong)
  python3 stale_check.py             # SO hash lưu ↔ hiện tại → in doc stale (chạy sau refresh-gitnexus.sh)

Repo root: /Users/tritdd/Work/ThreeSides. knowledge/ = <repo master_qa>/knowledge (đệ quy).
"""
import sys, re, hashlib, os, glob

ROOT = "/Users/tritdd/Work/ThreeSides"
REPO = {"backend": "threease_backend", "ticket": "threease_ticket", "pro": "threease_pro",
        "admin": "threease_admin", "reservation": "threease_reservation"}
KDIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../knowledge"))


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


def source_symbols(fm):
    out, in_block = [], False
    for line in fm.splitlines():
        if re.match(r"^source_symbols:", line):
            in_block = True
            out.extend(re.findall(r'"([^"]+)"', line))  # inline: source_symbols: ["a","b"] / []
            continue
        if in_block:
            m = re.match(r'^\s*-\s+"?(.+?)"?\s*$', line)
            if m:
                out.append(m.group(1).strip('"'))
            elif re.match(r'^\S', line):
                in_block = False
    return out


def file_for_symbol(sym):
    if ":" not in sym:
        return None
    key, rest = sym.split(":", 1)
    repo = REPO.get(key.strip())
    if not repo:
        return None
    path = re.split(r'[#(]', rest.strip())[0].strip()  # bỏ #symbol và (desc)
    return os.path.join(ROOT, repo, path) if path else None


def compute_hash(syms):
    files = sorted(set(f for f in (file_for_symbol(s) for s in syms) if f))
    if not files:
        return None
    h = hashlib.sha256()
    for f in files:
        h.update((open(f, 'rb').read() if os.path.exists(f) else b"MISSING:" + f.encode()))
    return h.hexdigest()[:16]


def stored_hash(fm):
    m = re.search(r'^source_hash:\s*(\S+)', fm, re.M)
    return m.group(1) if m else None


def main():
    update = "--update" in sys.argv
    docs = sorted(glob.glob(os.path.join(KDIR, "**", "*.md"), recursive=True))
    stale = []
    for path in docs:
        text = open(text_path := path, encoding="utf-8").read()
        fm = frontmatter(text)
        if not fm:
            continue
        syms = source_symbols(fm)
        new = compute_hash(syms)
        old = stored_hash(fm)
        rel = os.path.relpath(path, KDIR)
        if update:
            if re.search(r'^source_hash:', text, re.M):
                text = re.sub(r'^source_hash:.*$', f'source_hash: {new if new else "null"}', text, count=1, flags=re.M)
                open(path, "w", encoding="utf-8").write(text)
                print(f"  set  {rel:<34} source_hash={new}")
        else:
            if new is None:
                print(f"  --   {rel:<34} (no source_symbols — bỏ qua)")
            elif old in (None, "null"):
                print(f"  ??   {rel:<34} chưa có source_hash → chạy --update")
            elif old != new:
                stale.append(rel)
                print(f"  STALE {rel:<33} lưu={old} ↔ nay={new}")
            else:
                print(f"  ok   {rel:<34} {new}")
    if not update:
        print(f"\n→ {len(stale)} doc STALE" + (": " + ", ".join(stale) if stale else " (tất cả tươi)"))
        print("  (STALE = code source đổi → re-derive + re-confirm UI + --update lại)")


if __name__ == "__main__":
    main()
