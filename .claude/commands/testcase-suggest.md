# /testcase-suggest — Bộ não thiết kế test case (1a mù-code → 1b bind)

Sinh `tcs.json` (schema testcase-evidence) + `trace.json` từ spec ĐỘC LẬP.
Oracle = spec; 1a viết kỳ vọng khi mù code; 1b dùng GitNexus chỉ điền seam.

## Dùng
```
/testcase-suggest <folder>
```
Ví dụ: `/testcase-suggest wtf-is-this/TestCase_No.10.4`

## Chạy
```bash
source venv/bin/activate
python -c "from qa.suggest import suggest; import json; print(json.dumps(suggest('<folder>'), ensure_ascii=False, indent=2))"
```
- Nếu folder có `specs.html` mà chưa có `specs.md` → tự convert trước.
- In ra đường dẫn `tcs.json`/`trace.json` + **coverage** (section nào 0 case = lỗ hổng, báo user bổ sung).
- KHÔNG chạy test; dùng `/testcase-run` (pipeline sếp) để chạy sau.
