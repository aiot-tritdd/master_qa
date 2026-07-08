# /testcase-stale — phát hiện knowledge doc lỗi thời (staleness)

> Chạy **sau `refresh-gitnexus.sh`** (khi 5 repo update). So `source_hash` lưu trong mỗi
> `knowledge/**/*.md` với hash nội dung file source hiện tại → in doc nào **STALE** để re-confirm.
> Đây là **nhịp 2** của maintenance (refresh chỉ update graph, KHÔNG update knowledge — xem `docs/STATE.md`).

## Cách dùng
```
# 1) Sau khi pull + refresh-gitnexus.sh:
python3 .claude/skills-scripts/testcase-evidence/stale_check.py          # in list doc STALE

# 2) Sau khi đã re-derive + re-confirm UI doc stale (hoặc lúc grow doc mới xong):
python3 .claude/skills-scripts/testcase-evidence/stale_check.py --update # gắn/cập nhật source_hash
```

## Cơ chế (cơ khí, không reasoning)
- Mỗi doc có `source_symbols` (trỏ `repo: file#symbol` trong 5 repo). `source_hash` = hash nội dung
  các **file** đó lúc duyệt. Code đổi → file đổi → hash đổi → **STALE**.
- Surgical: chỉ doc chạm file vừa đổi mới stale — không đụng doc khác.
- Doc không có `source_symbols` (vd `observation-channels`, `system/OVERVIEW`) → bỏ qua (không track).

## Vòng maintenance đầy đủ
```
repo update → git pull → refresh-gitnexus.sh (graph tươi)
            → /testcase-stale            (tìm doc STALE)
            → với mỗi STALE: re-derive (GitNexus) + re-confirm (UI) → --update lại source_hash → approved
```

## Lưu ý
- Chạy `--update` **sau khi grow doc mới** (để có hash gốc) và **sau khi re-confirm** doc stale.
- Đây là **build-time tooling** — không phải QA-runtime. QA-runtime vẫn mù code.
