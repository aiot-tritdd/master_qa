# /testcase-compat — Test Compatibility (đa engine × đa viewport, black-box) một TestCase

Quét các màn spec đụng tới trên **nhiều browser engine × nhiều bề rộng màn hình**. **Track RIÊNG**,
KHÔNG trộn PASS/FAIL functional. Oracle = **chuẩn công bố + bất biến phổ quát** (không phải spec). Mù code.

## Cách dùng
`/testcase-compat wtf-is-this/TestCase-XX`

## TIẾT KIỆM TOKEN
Dùng lại `.claude/skills-scripts/testcase-evidence/`: `pw_lib` (nạp `.env`, `shot`),
`compat_lib` (`VIEWPORTS`, `BROWSERS`, `probeReflow/probeParity/probeConsole/detectTransient`, `verdict`, `finding`),
`build_compat_report.py`. KHÔNG viết lại. Setup 1 lần: `cd .claude/skills-scripts/testcase-evidence && npm i`.

## Nguyên tắc (2 tường)
- **Oracle = chuẩn phổ quát**, `specs.md` chỉ chọn màn (scope), KHÔNG làm oracle.
- **Mù code.** Chỉ quan sát DOM đã render + số đo layout + lỗi runtime.

## 3 oracle (vì sao track này 0-setup, hợp vision đa dự án)
| # | Oracle | Neo vào đâu | FAIL khi |
|---|---|---|---|
| 1 | **Reflow** | **WCAG 2.1 SC 1.4.10 (AA)** — W3C công bố, mốc **320 CSS px** | `scrollWidth > innerWidth` (+2px dung sai) ⇒ phải cuộn NGANG mới đọc hết |
| 2 | **Parity** | bất biến logic: cùng app ⇒ mọi engine phải bày CÙNG bộ affordance | engine nào thiếu/thừa nút-link-input so với engine tham chiếu |
| 3 | **No JS error** | `pageerror` (exception chưa bắt) = hỏng, không phải khác biệt thẩm mỹ | có ≥1 `pageerror` của chính app |

> Khác Visual: **KHÔNG cần baseline người-duyệt**, không mục rữa theo ngày — vì so **giữa các engine ở CÙNG
> một thời điểm**, không so với ảnh cũ. Đó là lý do Compatibility "drop-in" được, Visual thì không.

**Viewport** (`compat_lib.VIEWPORTS`): `mobile-320` (mốc WCAG) · `mobile-390` (iPhone 14/15) · `tablet-768` · `desktop-1280`.
**Engine** (`compat_lib.BROWSERS`): `chromium` · `firefox` · **`webkit`** *(= Safari = iPhone/iPad — với app CÔNG KHAI
cho khách thì đây là engine quan trọng NHẤT, không phải "cái thứ ba cho đủ bộ")*.

## 🚨 4 bẫy — đã cắn thật 2026-07-17, đọc trước khi chạy

**① KHÔNG được giả lập engine rồi báo "đã test".**
Máy hiện tại (**macOS 13.7.8**) → `Playwright does not support webkit on mac13` ⇒ **webkit = `未実施`**, ghi rõ lý do.
Giả lập iPhone bằng chromium (đổi viewport + UA) chỉ đổi **kích thước**, KHÔNG đổi **engine** — Safari có quirk
riêng (flexbox, `<input type=date>`, scroll). Báo "PASS Safari" kiểu đó = **PASS rỗng**. Muốn phủ thật: macOS ≥14,
hoặc webkit trong Docker/CI.

**② KHÔNG so `console.error` giữa engine — chỉ so `pageerror`.**
Đo thật: API 404 → **chromium** ghi `Failed to load resource: 404` ra console, **firefox KHÔNG ghi**. Cùng sự cố,
hai engine log khác nhau ⇒ đem console-error đi so parity là đang đo **cách browser ghi log**, không phải "app có
vỡ không" → chromium FAIL / firefox PASS = **kết luận BỊA**. Driver phải gắn `kind:'pageerror'|'console'`;
`probeConsole` tách `networkFailures` ra khỏi verdict (404 API là chuyện **functional**, không phải compat).

**③ Dialog chớp nhoáng làm parity tự mâu thuẫn.**
Đo thật: `button::閉じる` lúc firefox **thiếu** (320px), lúc firefox **thừa** (390px) — hai kết luận ngược nhau cho
cùng cặp engine ⇒ nhiễu thời điểm, không phải khác biệt engine. `detectTransient()` phát hiện (cùng key vừa thiếu
vừa thừa) → đưa vào `probeParity(sigs,{transient:[...]})`. ⚠️ Dao hai lưỡi: nhét bừa = **nuốt diff thật**. Chỉ thêm
khi đã CHỨNG MINH tự-mâu-thuẫn; `ignored` luôn được báo ra để người soi lại.

**④ Chờ ĐIỀU KIỆN, không chờ ĐỒNG HỒ.**
`waitForTimeout(7000)` làm widget ở desktop bị chấm `未実施` OAN — giây thứ 7 nó **vẫn đang loading** (spinner + lớp
phủ). Đo vỏ đang tải ≠ app vỡ. Dùng `getByText(<đặc trưng màn>).waitFor({state:'visible',timeout:30000})` +
`waitForLoadState('networkidle')`. (Luật này đã có sẵn ở `pw_lib.shot()` — dễ phạm lại.)

## Quy trình
1. **Scope:** `specs.md §3` → app/màn. Có `tcs.json` đã chạy → tái dùng màn/URL.
2. **Seam màn→URL:** `knowledge/*.md` approved. Chưa có → dừng, nhắc `/testcase-systemdoc`.
   ⚠️ **URL SAI = cả track vô nghĩa.** Widget reservation: đường vào thật là **`/<mã院>`** (vd `/2` → `AIoT院1`),
   KHÔNG phải `/reservation` — app hiểu path là **slug phòng khám**, nên `/reservation` đi tìm院 tên "reservation"
   → 404 toàn bộ API → widget rỗng data. Xác nhận vào ĐÚNG bằng **API 200 + tên phòng khám hiện ra**, không phải HTTP 200.
3. **Chạy** (driver inline): mỗi engine × viewport → mở màn (chờ điều kiện, xem bẫy ④) → thu:
   - `METRICS`: `scrollWidth`/`innerWidth` + `offenders` (phần tử thò khỏi mép phải — để chỉ đúng thủ phạm).
   - `SIG`: affordance ĐANG HIỆN `{role,name}` (button/a/input/select/textarea/[role=button|link]).
   - `errors`: `pageerror` + `console` (gắn `kind`).
   - Engine không launch được → **`未実施` + lý do**, KHÔNG bỏ lơ, KHÔNG giả lập.
4. **Chấm:** `verdict({reachable, reflow, parity, console})` → `PASS`/`FAIL`/`未実施`.
   ⚠️ Compat **KHÔNG BAO GIỜ** `SPEC-GAP` (chuẩn + bất biến luôn định nghĩa kỳ vọng).
5. **Viết `<folder>/compat.results.json`**:
   `{meta:{case,date,tester}, cells:[{browser,viewport,result,note}], parity:{<vp>:{summary}}, screens:[{name,app,url,result,findings,note}]}`
   Ô `未実施` **bắt buộc** có `note` = lý do thật.
6. **Factcheck rồi build:** `python3 .../factcheck_report.py <folder>/compat.results.json` → `python3 .../build_compat_report.py <folder>/compat.results.json <folder>/<Tên>.compat.xlsx`.
7. **Đẩy sổ bug** (chỉ FAIL): dedup **1 bug/(màn×họ×engine-class)** — tràn ở nhiều viewport cùng 1 nguyên nhân
   thì GOM 1 bug (như headers site-wide). `bug_type:"Compatibility"`, `result:"FAIL"`,
   `pri`= reflow/mất-affordance→High (chặn dùng), lỗi-JS→High, lệch nhỏ→Medium.
   `screen`="<App> — <Màn> (<engine>/<viewport>)", `before:null`+`note` lý do, `after`=ảnh. Build lại sổ.
8. **Báo cáo:** **ma trận engine × viewport**; nói RÕ engine nào `未実施` và VÌ SAO.
   ⚠️ **`未実施` không phải PASS** — đừng để người đọc tưởng đã phủ.

## Before final (checklist)
- [ ] Có đọc source code / `knowledge/system/**` / GitNexus không? **Đáp án đúng luôn là KHÔNG.**
- [ ] Có giả lập engine thiếu rồi báo như đã test không? **Phải là KHÔNG** — thiếu thì `未実施` + lý do.
- [ ] Verdict có dựa `console.error` không? **Phải là KHÔNG** — chỉ `pageerror` (bẫy ②).
- [ ] Đã vào ĐÚNG URL chưa (API 200 + data hiện ra), hay chỉ thấy HTTP 200 của vỏ SPA? (bẫy ở bước 2)
- [ ] Ô `未実施` đã ghi lý do thật chưa? Báo cáo có nói rõ engine chưa phủ không?
