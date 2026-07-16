# /testcase-systemdoc — Soạn Living Business Doc (BUILD-TIME, được đụng code)

> Tầng "người vẽ bản đồ". **Đây KHÔNG phải con QA.** Nó soạn tài liệu navigation cho QA đọc.
> Con QA-runtime (skill qa-brain) TUYỆT ĐỐI không chạy command này lúc test.

## Dùng
`/testcase-systemdoc <flow-id>`  — vd `/testcase-systemdoc issue-ticket-pack`

## Quy trình
1. **Structural (GitNexus):** `query({repo:"@threease", search_query})` + `context` để lấy
   facts: màn Nuxt / endpoint Django / job liên quan flow. GitNexus map tốt Nuxt/Django/jobs;
   luồng xuyên hệ (Pro→backend→ticket) graph **0 link** → trám bằng `CLAUDE.md` system-docs.
2. **Distill → nháp** `knowledge/<flow-id>.md`, `kind: flow` hoặc `channels`, `status: draft`,
   điền `source_symbols` + `source_hash` (metadata provenance).
3. **UI-confirm bằng explorer (tự-lái, thay cho click tay):**
   - `node explorer.js snapshot --target <t> --url <path>` → Claude THẤY trang bằng chữ (a11y-tree).
   - Claude soạn step-list JSON (role/name/label/text; toạ độ CHỈ khi bất khả kháng + `fragile:true`).
   - `node explorer.js run --steps steps.json --target <t> --url <path>` → per-step báo chỗ gãy → vá → lặp.
   - `node explorer.js replay --steps steps.json --target <t> --url <path> --shot shots/confirm.png`
     → nghiệm từ session SẠCH → **1 ảnh tới điểm quan sát** (người liếc để duyệt).
   - `node explorer.js dynamic --target <t> --url <path>` → liệt kê vùng ĐỘNG (đồng hồ/tên/số dư — chụp
     màn 2 lần cùng-trạng-thái, diff pixel) kèm best-effort selector. Claude liếc + chọn selector che.
     Đây là cách sinh `mask:` cho **Visual regression** (KHÔNG mask tay lúc `/testcase-visual`). Mask là HOW
     (quan sát ổn định) → KHÔNG phá FIREWALL. Động xuyên-phiên (số dư mai khác) → Claude bổ sung tay lúc duyệt.
   - `node explorer.js emit --flow <flow-id> --steps steps.json --symbols "repo: path||repo: path2" --mask "sel1||sel2"`
     → nhả navigation block (HOW-only) + khối `mask:` vào `knowledge/<flow-id>.md`. Điền `ui_confirmed_at`.
     (`--mask` tuỳ chọn — bỏ qua nếu màn không có vùng động.)
   - Chạy `python3 stale_check.py --update` để điền `source_hash`.
   (explorer = `.claude/skills-scripts/testcase-evidence/explorer.js`, BUILD-TIME only; cấm ở `/testcase-run`.)
4. **Người duyệt** → liếc `shots/confirm.png` + block → đổi `status: draft → approved`.
   Chỉ doc `approved` mới cho QA tin.

## FIREWALL (bắt buộc)
Doc CHỈ ghi **cách vận hành (HOW) + nơi quan sát**. **CẤM** ghi kết quả kỳ vọng / luật pass-fail
(đó là SPEC + quan sát live của QA). `source_symbols/source_hash` = metadata, QA không đọc.

## Staleness
Code đổi → `source_hash` lệch → gắn `status: stale` → phải re-derive (bước 1–2) + re-confirm UI
(bước 3) + duyệt lại trước khi QA tin.
