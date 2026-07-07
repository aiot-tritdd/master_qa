from html.parser import HTMLParser
from pathlib import Path


class _Md(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []
        self._skip = 0          # bên trong script/style

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in ("h1", "h2", "h3", "h4"):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in ("li",):
            self.out.append("\n- ")
        elif tag in ("p", "br", "tr", "div"):
            self.out.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        elif tag in ("h1", "h2", "h3", "h4", "p"):
            self.out.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        text = " ".join(data.split())
        if text:
            self.out.append(text)


def html_to_markdown(html: str) -> str:
    p = _Md()
    p.feed(html)
    md = "".join(p.out)
    lines = [ln.rstrip() for ln in md.splitlines()]
    result: list[str] = []
    for ln in lines:
        if ln == "" and result and result[-1] == "":
            continue
        result.append(ln)
    return "\n".join(result).strip() + "\n"


def ingest(folder: Path) -> Path:
    folder = Path(folder)
    md_path = folder / "specs.md"
    html_path = folder / "specs.html"
    if not html_path.exists():
        raise FileNotFoundError(f"không thấy {html_path}")
    md_path.write_text(html_to_markdown(html_path.read_text()), encoding="utf-8")
    return md_path
