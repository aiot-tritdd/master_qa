# /testcase-stale — Dò spec/case đã lệch code

## Dùng
```
/testcase-stale <folder>
```

## Chạy
```bash
source venv/bin/activate
python -c "from qa.stale import check_stale; import json; print(json.dumps(check_stale('<folder>'), ensure_ascii=False, indent=2))"
```
TC nào `stale:true` → spec/case có thể không còn khớp code → người xem lại spec.
