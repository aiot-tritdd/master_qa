# explorer.js — Bộ dò-đường tự-lái cho UI-confirm (build-time)

> **Loại:** Design spec (brainstorming output) · **Ngày:** 2026-07-14 · **Trạng thái:** chờ duyệt
> **Liên quan:** `/testcase-systemdoc` (bước 3 "UI-confirm mỏng") · `pw_lib.js` (tái dùng `getPage`) ·
> `stale_check.py` (nối metadata) · README §6 (2 pha) §10 (grow demand-driven) §12 (HOW/WHAT).
> **Nguyên tắc ưu tiên:** **#1 Máy không bao giờ thành oracle** (SPEC vẫn là oracle) ·
> **#2 Máy làm phần cơ khí + phán đoán HOW; người chỉ confirm nhẹ.**

---

## 1. Vấn đề (vì sao có dự án này)

Mỗi spec mới cần một flow **chưa-approved** để dựng precondition → buộc phải **UI-confirm** flow đó
(pha build-time, `/testcase-systemdoc` bước 3). Hôm nay bước đó **không có đồ nghề**: chỉ ghi "dùng
`pw_lib` click 1 lần". Thực tế (14/07, obs `3683`→`3689`) nó biến thành vòng lặp **mù**:

```
viết cả file .js → chạy headless → nhìn 1 tấm PNG → đoán sai → viết lại cả file → ...
```

7 script cho MỘT flow, và thụt lùi từ selector ngữ nghĩa → **coordinate-sweep 35 điểm** (toạ độ gãy
ngay khi layout đổi → dò lại). Đây là **nút thắt lặp lại mỗi lần chạm domain mới** (Booking / Reservation
widget / Admin còn chưa approved), không phải sự cố lẻ.

**Mục tiêu:** máy **tự dò + tự lái + tự nghiệm** rồi đưa kết quả; người **confirm nhẹ** (liếc 1 ảnh).
KHÔNG bắt người tìm đường tay, KHÔNG bắt người review nặng.

### Không làm gì (YAGNI)
- Không MCP, không process sống dai / REPL, không agent tự-heuristic.
- Không tự ghi **WHAT** (kết quả kỳ vọng / pass-fail) — đó là SPEC + quan sát live của QA.
- Không **tự duyệt** — người vẫn flip `status: draft→approved`.
- Không "phép màu hoá" ô-lịch-trống — xử bằng luật gắn cờ (§5), không giả vờ a11y cứu được.
- Không đụng `/testcase-run` / evidence / Excel — đây là đồ nghề **build-time**, tách hẳn runtime.

---

## 2. Nền tảng đã chứng minh (không xây từ đầu)

Playwright 1.61.1 (đã cài) cho **native**, không cần dependency mới:

```
$ ariaSnapshot() trên <button>追加</button><label>お客様<select>…</label><div role=tab>チケット</div>
- button "追加"
- combobox "お客様":
  - option "KH3" [selected]
- tab "チケット"
```

Tức "danh sách element có tên bằng CHỮ" là **native**. `getByRole({name})` / `getByLabel` chạy. →
explorer chỉ **bọc mỏng**, không phát minh lại.

---

## 3. Kiến trúc: Claude = ĐẦU, explorer = TAY

Theo nguyên tắc token (session ấm nghĩ, script làm cơ khí): **không** nhồi heuristic tự-đoán vào
script (tránh đẻ agent dở). Claude nghĩ, `explorer.js` thực thi.

### 3.1 Bộ nguyên thủy (`explorer.js`, cạnh `pw_lib.js`)

| Primitive | Làm gì | Dựa trên |
|---|---|---|
| `snapshot(page[, region])` | trả cấu trúc trang bằng **chữ** | `locator.ariaSnapshot()` |
| `act(page, step)` | bấm/điền theo **tên/role/nhãn** | `getByRole` / `getByLabel` / `getByText` |
| `nearLabel(page, label)` | tìm control gần nhãn (ca dropdown お客様, obs `3687`) | bounding-box y-distance |
| `replay(target, steps)` | chạy lại danh sách bước từ **session SẠCH** (`NO_STATE`) | `pw_lib.getPage` |

Tất cả tái dùng `pw_lib.getPage(target)` → login/locale(`ja-JP`)/viewport/session giữ nguyên,
không giải lại.

### 3.2 Vòng lặp (Claude lái, explorer báo per-step)

```
1. explorer.snapshot 1 phát        → Claude THẤY landing page bằng chữ (hết mù)
2. Claude soạn danh sách bước ngữ nghĩa (step-list JSON) hướng tới đích
   (mồi từ draft GitNexus của systemdoc + snapshot bước 1)
3. explorer chạy list → trả per-step: {ok|fail, snapshot-tại-chỗ-gãy}
4. Claude vá ĐÚNG bước gãy → chạy lại   (lặp; mỗi vòng có CHỮ ⇒ hội tụ nhanh)
5. Đạt đích → explorer.replay(list) từ session sạch → 1 ảnh tới điểm quan sát
6. explorer nhả: navigation block + metadata (§4)
```

**Step-list schema (nháp, chốt lúc plan):**
```json
{ "target": "pro",
  "goal": "mở form booking + thêm vé AIOT-TEST-TK10",
  "steps": [
    { "action": "click", "role": "button", "name": "アイテムを追加" },
    { "action": "click", "role": "tab", "name": "チケット" },
    { "action": "fill", "label": "お客様", "value": "AIOTTEST-KH3", "via": "nearLabel" },
    { "action": "click", "text": "AIOT-TEST-TK10" }
  ] }
```

Khác 14/07: mỗi vòng nhận **chữ** (thấy chỗ gãy) thay vì **ảnh mù**; Claude vá **1 bước** thay vì
viết lại **cả file**.

---

## 4. Đầu ra

1. **navigation block** — step-list đã nghiệm (locator bền + điểm quan sát) → dán vào
   `knowledge/<flow>.md`. **CHỈ HOW.**
2. **metadata tự điền** — `source_hash` (nối `stale_check.py`), `ui_confirmed_at`, `source_symbols`.
   Thuần cơ khí, không phán đoán ⇒ an toàn tự động.
3. **1 ảnh replay-thành-công** (tới điểm quan sát) — cho người liếc.

---

## 5. Bức tường: máy KHÔNG bao giờ thành oracle — ép bằng CẤU TRÚC

- navigation block **không có ô** cho "kết quả kỳ vọng" → máy **vật lý** không ghi WHAT được. Nó log
  vị trí (*"tới màn có tab 会計"* = HOW), **cấm** phán quyết (*"snackbar hiện X nên đúng"* = WHAT).
  → FIREWALL của `/testcase-systemdoc` còn nguyên.
- **Bước không làm được bằng tên** (ô lịch trống) → được phép dùng toạ độ **NHƯNG bắt buộc gắn cờ**
  `fragile: coordinate` trong step, không lén đóng dấu như locator sạch. Luật của máy, không phải
  việc của người.
- Oracle vẫn là **SPEC** (người viết 1 lần). explorer chỉ chạm **HOW**; đúng/sai vẫn là SPEC + quan
  sát live của QA-runtime.

---

## 6. Người "confirm nhẹ" đúng nghĩa

Liếc **một** ảnh replay-đã-tới-điểm-quan-sát → gật → đổi `status: draft→approved`. Hết.
Không đọc prose, không dò toạ độ. Neo an toàn = **một lần chạy lại tái lập được từ session sạch**
(nghiệm bằng THỰC THI), không phải lời máy.

---

## 7. Chỗ cắm & ranh giới pha

- explorer = **cơ bắp cho `/testcase-systemdoc` bước 3**. Bước 3 đổi từ "dùng pw_lib click 1 lần"
  → "chạy explorer tới đích; nó lái + tự nghiệm + nhả navigation block; người liếc ảnh replay + duyệt".
- **Build-time only.** Đây là một **biên công cụ rõ** → dọn đường cho (a): PreToolUse hook về sau chỉ
  việc cấm `explorer.js` + GitNexus + `knowledge/system/` + đọc code trong `/testcase-run`.
  **(b) vẽ biên; (a) dựng rào lên biên đó.**

---

## 8. Rủi ro & giả định

- **ô-lịch-trống** vẫn cần toạ độ (a11y không thấy cell trống là element) → luật gắn cờ §5 chấp nhận
  ngoại lệ hiếm, không lây ra cả flow.
- **Vuetify re-render / detach** giữa chừng — `pw_lib.fillSafe` đã có mẫu retry; `act()` kế thừa.
- **Harness-stale** (locale/viewport đổi → nhãn UI đổi mà `source_hash` không bắt) — vẫn theo luật
  KNOWLEDGE-STRATEGY §3: đổi harness → re-UI-confirm. explorer làm việc re-confirm đó **rẻ đi**, không
  thay được nhịp kiểm.
- **Giả định:** flow test-tới đều có đích quan sát được bằng a11y-name; nếu không → SPEC-GAP/未実施 ở
  tầng QA, ngoài phạm vi explorer.
