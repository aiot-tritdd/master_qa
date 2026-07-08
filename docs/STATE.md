# STATE — điểm dừng & việc tiếp (đọc ĐẦU TIÊN mỗi phiên)

> File **sống** — cập nhật cuối mỗi phiên. Mục đích: mở phiên mới là biết ngay *đang ở đâu, làm gì tiếp*.
> Cập nhật: **2026-07-08**. Branch git: `qa-brain` (threease_qa).

---

## 0. Đọc theo thứ tự để nắm hệ thống

`docs/STATE.md` (file này) → `CLAUDE.md` → `docs/QA-SERVER.md` (kinh thánh) →
`docs/KNOWLEDGE-STRATEGY.md` → `knowledge/system/OVERVIEW.md`.

## 1. Hệ thống LÀ GÌ (1 dòng)

QA senior **black-box** (skill `qa-brain` + commands `testcase-*`): SPEC → sinh+chạy test trên **dev** →
evidence PNG/xlsx. Oracle = SPEC + quan sát live. **Mù code.** GitNexus chỉ ở build-time (soạn knowledge).

## 2. ĐÃ XONG (đừng làm lại)

- ✅ **Redesign black-box** đã adapt TOÀN BỘ: SKILL.md · commands · `build_evidence.py` (3-sheet template) ·
  `pw_lib.js` (targets pro/ticket/ticket_admin/reservation/admin) · docs · 2× CLAUDE.md. Spec/plan ở `docs/plans/2026-07-07-*`.
- ✅ **Chuẩn evidence:** xlsx 3 sheet (Cover/Test Cases/Checklist+Nguồn), **mỗi case 2 ảnh before+after PNG rõ**.
- ✅ **Skill `/specs-md`** (html→md).
- ✅ **knowledge/** (nav, approved): `observation-channels` · `pro-open-booking` (mở booking+cancel payment/cancel/delete/remove) · `ticket-coupon-reports`. Draft: `issue-ticket-pack`.
- ✅ **knowledge/system/** (business toàn hệ, mới): `OVERVIEW.md` (8 domain) + `customer-sync.md`.
- ✅ **Test đã chạy:** `TestCase_NEW` (thu hồi vé) 7 case verified · `TestCase-11` (coupon report) **9 PASS/8 FAIL**, khớp 100% scope dev.
- ✅ Docs sync hết (STATE/DEMO/QA-SERVER/KNOWLEDGE-STRATEGY + 2 CLAUDE.md).

## 3. VIỆC TIẾP (ưu tiên trên xuống)

1. ✅ **[GĐ-0] Khép vòng maintenance — XONG (2026-07-08):** `stale_check.py` + lệnh **`/testcase-stale`** +
   `source_hash` thật trên doc có `source_symbols`. Dùng: sau `refresh-gitnexus.sh` → `/testcase-stale` →
   re-confirm doc stale → `stale_check.py --update`. → **Việc tiếp thực sự bắt đầu từ #2.**
2. **[Grow knowledge/system] domain deep-dive** — ✅ `customer-sync` + ✅ `payment-cancel` (2026-07-08).
   ✅ `ticket-issue-sync` ✅ `coupon-sc` (Reports gộp vào coupon-sc + `ticket-coupon-reports`). **Còn 3:** Booking · Reservation widget · Admin (cần GitNexus-read fresh — xem `OVERVIEW.md`).
3. **[Nav doc]** Nâng `issue-ticket-pack.md` draft→approved: UI-confirm khâu **tạo booking→thanh toán→phát hành vé** (chưa drive đủ).
4. **[Optional]** `TestCase_NEW`: 6 case còn 未実施 cần precondition **gói vé còn nguyên** (KH3 đã dùng 2 vé) → phải dựng booking mới.

## 4. Cách maintain khi 5 repo update

`refresh-gitnexus.sh` (graph tươi — CHỈ graph) → **stale-check `source_hash`** → re-confirm CHỈ doc drift.
⚠️ refresh KHÔNG tự update knowledge/. (Lệnh stale-check = việc #1 ở trên.)

## 5. Access nhanh (dev) — để chạy ngay

- Creds: `wtf-is-this/account.txt`. `pw_lib`: `getPage('pro'|'ticket'|'ticket_admin'|'reservation'|'admin')`.
- **Report ticket cần** `TESTSEED001/ticket-admin/password123` → env `TK_STAFF=ticket-admin`.
- Data test: prefix `AIOT-TEST-*`/`AIOTTEST*` → `/testcase-cleanup`. Dev có test data: customer `AIOTTEST-KH3` (booking 07/13 + gói vé).
- Build xlsx: `python3 .claude/skills-scripts/testcase-evidence/build_evidence.py <F>/tcs.json <F>/<Tên>.xlsx`.

## 6. NGUYÊN TẮC BẤT DI (đừng phá — đã từng trả giá)

1. Oracle = **SPEC**; viết `expect` MÙ code.
2. QA-runtime **mù code, không GitNexus**; FAIL báo **hành vi + ảnh**, không symbol/file:line.
3. **KHÔNG code-trace để phán "đã build/chưa"** — đã SAI (guard vé-đã-dùng). Dùng `route_map` (build-time) + quan sát live.
4. knowledge = navigation (HOW), KHÔNG phải oracle. Graph→draft; UI-confirm→approved.
5. Specs sau này = **tinh chỉnh/update** business đã map, không build lại từ 0.

## 7. Trạng thái git / task nền

- Branch `qa-brain`; các thay đổi redesign/knowledge/docs đã commit. `wtf-is-this/` đã **gitignore** (evidence local).
- Đống transition Python→skill (`D qa/ api/ web/ tests/`) còn trong index — **để user tự xử** (chưa commit).
- Không có background task đang chạy.
