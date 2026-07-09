#!/usr/bin/env python3
"""Lọc file spec HTML -> text gọn để Claude đọc rẻ token.

Cách dùng: python3 html_to_text.py <file.html> [out.txt]
- Bỏ script/style/head, giữ text theo thứ tự DOM.
- Bảng (<table>) xuất dạng markdown; heading giữ mức (#, ##...).
- Link giữ dạng [text](href); ảnh chỉ ghi tên (không base64).
"""
import sys, re
from html.parser import HTMLParser


class Extractor(HTMLParser):
    SKIP = {'script', 'style', 'head', 'meta', 'link', 'noscript'}
    H = {'h1': '# ', 'h2': '## ', 'h3': '### ', 'h4': '#### ', 'h5': '##### ', 'h6': '###### '}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0
        self.buf = ''
        self.href = None
        self.in_table = False
        self.row = None
        self.table = None

    def flush(self):
        t = re.sub(r'\s+', ' ', self.buf).strip()
        if t:
            self.out.append(t)
        self.buf = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP:
            self.skip += 1
            return
        if tag in self.H:
            self.flush(); self.buf = self.H[tag]
        elif tag in ('p', 'div', 'br', 'section', 'article'):
            self.flush()
        elif tag == 'li':
            self.flush(); self.buf = '- '
        elif tag == 'a':
            self.href = a.get('href')
        elif tag == 'img':
            alt = a.get('alt') or (a.get('src') or '')[:60]
            self.buf += f' [img: {alt}] '
        elif tag == 'table':
            self.flush(); self.in_table = True; self.table = []
        elif tag == 'tr' and self.in_table:
            self.row = []
        elif tag in ('td', 'th') and self.in_table:
            self.buf = ''

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if tag == 'a' and self.href and self.buf.strip():
            self.buf += f' ({self.href})'
            self.href = None
        elif tag in ('td', 'th') and self.in_table and self.row is not None:
            self.row.append(re.sub(r'\s+', ' ', self.buf).strip()); self.buf = ''
        elif tag == 'tr' and self.in_table and self.row is not None:
            self.table.append(self.row); self.row = None
        elif tag == 'table' and self.in_table:
            self.in_table = False
            rows = [r for r in (self.table or []) if any(c for c in r)]
            if rows:
                w = max(len(r) for r in rows)
                for i, r in enumerate(rows):
                    r += [''] * (w - len(r))
                    self.out.append('| ' + ' | '.join(r) + ' |')
                    if i == 0:
                        self.out.append('|' + '---|' * w)
            self.table = None
        elif tag in self.H or tag in ('p', 'div', 'li', 'section', 'article'):
            self.flush()

    def handle_data(self, data):
        if not self.skip:
            self.buf += data


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = open(sys.argv[1], encoding='utf-8', errors='replace').read()
    ex = Extractor(); ex.feed(src); ex.flush()
    text = '\n'.join(ex.out)
    text = re.sub(r'\n{3,}', '\n\n', text)
    if len(sys.argv) > 2:
        open(sys.argv[2], 'w', encoding='utf-8').write(text)
        print(f'saved {sys.argv[2]} ({len(text)} chars, từ {len(src)} chars HTML)')
    else:
        print(text)


if __name__ == '__main__':
    main()
