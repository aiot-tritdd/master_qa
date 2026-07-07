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
3. **BẮT BUỘC UI-confirm mỏng:** dùng `pw_lib.getPage(...)` click thật qua flow 1 lần để xác
   nhận các bước/nút đúng app thật. Điền `ui_confirmed_at`.
4. **Người duyệt** → đổi `status: draft → approved`. Chỉ doc `approved` mới cho QA tin.

## FIREWALL (bắt buộc)
Doc CHỈ ghi **cách vận hành (HOW) + nơi quan sát**. **CẤM** ghi kết quả kỳ vọng / luật pass-fail
(đó là SPEC + quan sát live của QA). `source_symbols/source_hash` = metadata, QA không đọc.

## Staleness
Code đổi → `source_hash` lệch → gắn `status: stale` → phải re-derive (bước 1–2) + re-confirm UI
(bước 3) + duyệt lại trước khi QA tin.
