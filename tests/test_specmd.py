from qa.specmd import html_to_markdown


def test_strips_tags_and_keeps_text():
    html = "<h1>Tiêu đề</h1><p>Đoạn văn</p><script>bad()</script>"
    md = html_to_markdown(html)
    assert "Tiêu đề" in md
    assert "Đoạn văn" in md
    assert "bad()" not in md
    assert "<" not in md


def test_heading_becomes_hash():
    md = html_to_markdown("<h2>Yêu cầu</h2>")
    assert md.strip().startswith("#")
    assert "Yêu cầu" in md


def test_list_items_become_dashes():
    md = html_to_markdown("<ul><li>một</li><li>hai</li></ul>")
    assert "- một" in md
    assert "- hai" in md
