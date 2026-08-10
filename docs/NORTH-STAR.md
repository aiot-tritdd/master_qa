# NORTH-STAR — master_qa: đích · đang ở đâu · đang là gì

> **La bàn của cả dự án.** Mở file này ra là biết ngay: *(1) mình đang hướng tới cái gì (target state),
> (2) mình đang đứng chỗ nào trên bản đồ đó, (3) mình hiện là cái gì.* Đây là thứ giữ mọi quyết định
> nhỏ đi cùng một hướng — để agent #10 hôm nay cắm vừa vào chỗ agent #11, #12 ngày mai.
>
> **Đọc cùng bộ 3:**
> - `NORTH-STAR.md` (file này) = **ĐÍCH + la bàn** (đổi khi *hướng* đổi, không phải mỗi phiên).
> - `STATE.md` = **ĐANG Ở ĐÂU** ngay lúc này (file sống, cập nhật cuối mỗi phiên).
> - `ROADMAP.md` = **ĐƯỜNG ĐI** chi tiết theo lưới Level × Type.
> - `README.md` = **hệ nghĩ gì / vận hành sao** (giải thích đầy đủ).
>
> Cập nhật: **2026-08-10** (pentest lớp P1 đóng trọn — mũi nhọn đầu = auth/session, live 2× CONFIRMED).
> Lập file: 2026-08-06 (chốt tầm nhìn master_qa đa-agent + khởi động pentest agent).

---

## 0. Nguyên tắc vàng khi vận hành (đọc trước)

**Agent (Claude) LUÔN phải biết 3 điều trước khi làm bất cứ gì:**

1. **Đích** — target state ở §2. Việc đang làm phải *cắm vừa* vào bản đồ đó.
2. **Đang ở đâu** — snapshot ở §3 + `STATE.md`. Không bịa "đã có/chưa có" bằng suy đoán code.
3. **Đang là gì** — danh tính ở §1. Đừng phản bội 2 bức tường thép (black-box, oracle độc lập).

> Về sau (phase sau) mỗi lần làm xong một việc, mình sẽ **cập nhật / biến tấu bản đồ này dần** cho khớp
> thực tế học được. Hiện tại điều quan trọng nhất: **mở file này ra là định vị được ngay**, không lạc.

---

## 1. Danh tính — master_qa LÀ gì, đang TRỞ THÀNH gì

**Là gì hôm nay:** một **QA senior nhân tạo, mù code, black-box** — đưa SPEC, nó tự lái app dev,
quan sát bằng mắt, chấm PASS/FAIL kèm evidence. Oracle = **SPEC + quan sát live**, không bao giờ từ code.
(Chi tiết đầy đủ: `README.md`.)

**Đang trở thành:** một **HỆ THỐNG QA đa-agent, tái dùng cho MỌI dự án** — nhiều agent, mỗi agent
chuyên một mảng, đứng dưới một nhạc trưởng (orchestrator) điều phối. Con QA black-box hôm nay là
**agent đầu tiên** của hệ đó; 9 lệnh type-track hiện tại là **9 chuyên gia phôi thai**.

> Đổi tên: **`threease_qa` → `master_qa`** — **HOÀN TẤT 2026-08-06**. Đã di dời: thư mục, toàn bộ
> docs/comment, workspace `CLAUDE.md`, git remote URL, GitNexus `registry.json`, **repo GitHub
> `aiot-tritdd/master_qa`, và đã `git push`** (commit `ed717ee`). `group.yaml` không đụng
> (qa không thuộc group `threease`).

---

## 2. TARGET STATE — kiến trúc đích (la bàn dài hạn)

> Đây là **hình dạng master_qa sẽ CÓ khi trưởng thành**, KHÔNG phải thứ xây ngay. Nó là **la bàn,
> không phải hợp đồng** — sẽ vẽ lại khi học ra điều mới. Đây **không** phải hạ tầng máy chủ; nó là
> **bản đồ logic**: ai-là-agent, ai-gọi-ai, evidence chảy đường nào. (Docker stack của sản phẩm là
> *target bị test*, nằm NGOÀI bản đồ này.)

```
   Target (URL / app)  ───►  ┌─────────────────────────────┐
   + đầu vào phù hợp          │   master_qa ORCHESTRATOR     │  ── chọn agent nào chạy, gom evidence,
   (SPEC / scope+account...)  │   (router · nhạc trưởng)     │      khử trùng lặp, xuất 1 báo cáo hợp nhất
                              └──────────────┬──────────────┘      [CHƯA XÂY — chỉ xuất hiện khi ≥2 agent đủ khỏe]
                                             │ dispatch
        ┌───────────────┬───────────────┬────┴──────────┬───────────────┐
        ▼               ▼               ▼               ▼               ▼
   functional        a11y          security          perf        i18n · compat · visual …
   (oracle=SPEC)   (oracle=WCAG)  (bất biến an ninh) (Core Web Vitals)   ✅ ĐÃ CÓ (9 type-track hôm nay,
                                                                            dạng lệnh rời — chưa gắn nhạc trưởng)
                                        │
                                        ▼  ← agent MỚI đang thiết kế (specialist #10)
                                 ┌──────────────┐
                                 │ PENTEST agent │  ← bản thân là 1 HỆ CON (fractal):
                                 └──────┬────────┘
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
                       black-box     grey-box      white-box
                    (recon-skills   (dockerscan/   (Semgrep/
                     + kỹ thuật web) infra scan)    CodeQL, SAST)
                    oracle = TÁI HIỆN  ← LÀM TRƯỚC   ← để dành các phase sau
                    được tấn công
```

**Đầu vào KHÁC nhau tùy agent** — điểm dễ nhầm:
- 9 agent QA cũ: đầu vào = **SPEC** (có "đáp án đúng" để so).
- **pentest**: **KHÔNG dùng SPEC** — không có SPEC nói "chỗ này phải chặn IDOR". Đầu vào =
  **Target URL + scope + tài khoản test**. Oracle của nó = **tái hiện được một kịch bản tấn công gây hại**,
  không phải "so với SPEC".

**"Chạy bằng gì" (infra của chính master_qa):** KHÔNG cần hạ tầng riêng cho các phase đầu. Engine =
**Claude Code + cơ chế subagent có sẵn**; mỗi specialist = một skill/subagent; evidence = **file trên đĩa**
(PNG/md/xlsx). Không dựng server, không DB riêng. → Triết lý: **"harvest, đừng host"** (xem §5).

---

## 3. ĐANG Ở ĐÂU — snapshot (nguồn sống: `STATE.md`)

- **9 type-track** đã build: functional · a11y · visual · security · compat · perf · i18n(type-7) đều
  black-box; **load/stress** grey-box/SRE (RUN-GATED, chưa bắn). Phủ **3/5 app** (ticket·pro·reservation;
  admin bỏ hẳn; backend không UI).
- **Orchestrator (nhạc trưởng): CHƯA có.** 9 track vẫn là lệnh rời. Đúng kế hoạch — nhạc trưởng chỉ
  xuất hiện khi đã có ≥2 agent đủ khỏe để điều phối (tránh premature abstraction).
- **Pentest agent (specialist #10): ĐÃ BUILD — lớp P1 đóng trọn, live-verified** (§4). Black-box leaf: khung
  pipeline ~90% + lớp **P1 (auth/session revocation & replay)** xong cả 2 nửa — **P1a access-token + P1b
  refresh-token + continuity gate** — chạy thật trên `stg-monomana`, **2× CONFIRMED** (verdict do code tự chấm).
  Độ phủ lỗ hiện ~1 lớp / ~8. Grey/white-box: chưa. Chi tiết + việc tiếp: §4.

---

## 4. ĐANG LÀM GÌ — Giai đoạn 1: PENTEST agent (black-box, standalone)

**Mục tiêu (lời sếp):** làm nhanh · standalone trước · **xem hiệu quả thế nào** · rồi expand dần &
tích hợp vào hệ. Goal cuối: test được **nhiều dự án**.

**Hình dạng giai đoạn 1:** một skill `/pentest <url>` — gõ là chạy — chỉ làm **1 chiếc lá black-box**
của cây pentest. Chưa đụng orchestrator, chưa grey/white.

**Các quyết định đã CHỐT:**

| Quyết định | Chốt |
|---|---|
| **Trường phái** | Black-box qua URL trước (khớp "nhiều dự án" + triết lý code-blind). Grey/white để dành. |
| **Scope/authorization** | **CHỈ target mình sở hữu / dev-staging.** Không bắn target người khác. |
| **Oracle (luật cứng)** | **"No evidence, no finding"** — cấm ghi finding trừ khi đính được **cặp request→response tái hiện** chứng minh tác hại. |
| **3 mức tin cậy** | `CONFIRMED` (đã tái hiện, có bằng chứng → mới là finding) · `SUSPECTED` (có tín hiệu, chưa chứng minh → đưa người) · `INFO` (vệ sinh/cấu hình → context, KHÔNG thổi thành lỗ hổng). |
| **Đánh đổi** | **Nghiêng hẳn PRECISION** — thà báo ÍT finding mà thật, còn hơn nhiều finding hào nhoáng nửa số ảo. "Hiệu quả" = tỉ lệ finding thật / tổng, không phải số lượng. |
| **Workflow** | `recon → enumerate → test → confirm (tái hiện) → report`. |
| **Mũi nhọn lớp lỗ đầu tiên** | **auth/JWT/session (P1)** — ĐÃ CHỐT & ĐÓNG TRỌN. (Ban đầu định IDOR, nhưng thiếu `TESTSEED002` → lấy **phương án B = session/token** làm đường CHÍNH: tái hiện sạch chỉ với 1 tài khoản, an toàn dev.) IDOR lùi thành **P2**. |
| **Target thử đầu** | `https://stg-monomana.aiotso.net` (owner-authorized staging; account `demo@dx-aiot.com`). Stack dev ThreeSides (`pro :8080` + backend `:3000`) để dành cho các run sau. |

**HOÃN có chủ ý (không phải bỏ):** SSRF (cần callback infra) · SQLi/injection (rủi ro mutate data dev) ·
XSS (khó auto-confirm tác hại) · business-logic race coupon/points (giá trị cao, khó chuẩn hóa). Thêm dần
khi mũi nhọn đầu đã chứng minh hiệu quả.

**Lộ trình lớp lỗ (catalog — nhiều version, expand dần):**

| Lớp | Là gì | Trạng thái |
|---|---|---|
| **P1** | auth/session revocation & replay (P1a access + P1b refresh + continuity) | ✅ **ĐÓNG TRỌN** — live 2× CONFIRMED (v1.0 + v1.1) |
| **P2** | IDOR / horizontal BAC | ⏸ **KẸT DATA** — cần `TESTSEED002` (tenant-2); không có cặp "token A + ID của B" → chưa tái hiện được. **Phải xin `TESTSEED002` từ dev/sếp.** |
| **P3** | privilege escalation / vertical BAC | 🔜 có thể làm **không cần tenant-2** (1 route admin-only + 1 account user) — ứng viên "việc tiếp" nếu P2 còn kẹt data |
| deferred | SSRF · SQLi/injection · XSS · business-logic race | ⬜ v2+ (mở dần khi lớp trước chứng minh hiệu quả) |

**Bước kế tiếp (§ "việc tiếp"):** P2 IDOR **ngay khi có `TESTSEED002`**; nếu data còn kẹt → mở **P3
priv-esc** (không cần tenant-2). Mỗi lớp mới = harvest ~1 recipe + viết 1 oracle, KHÔNG đụng khung.

---

## 5. Nguyên tắc vận hành (giữ hướng khi thiết kế)

- **Harvest, đừng host.** Đã có engine (Claude Code) + khung QA. Cái thiếu là **kiến thức tấn công** +
  **kỷ luật bằng chứng**. → Thu hoạch `uphiago/recon-skills` (145 SKILL.md, format Claude Code, MIT) làm
  kho kiến thức black-box; copy kỷ luật `confirm_finding`/evidence của `PentesterFlow/agent` (đừng nuốt
  cả con — nó là agent riêng, sẽ rẽ nhánh). KHÔNG dùng `Raccoon` (stale) / `GhidraGPT` (lạc đề, binary).
- **YAGNI — hệ thống KẾT TINH, không xây trước.** Không dựng orchestrator trước khi có agent để điều phối.
  Xây 1 agent cho khỏe → thêm agent → nhạc trưởng xuất hiện mỏng dính sau cùng.
- **2 bức tường thép giữ nguyên cho các agent QA:** black-box + oracle độc lập với code. Ngoại lệ có chủ
  ý: grey-box/SRE (load/stress) và **grey/white-box của pentest** — chúng sống như track riêng, tách khỏi
  con đen mù code, không lẫn vào.
- **Đừng code-trace để phán "đã build/chưa".** Dùng quan sát thật + `STATE.md`. Đã sai một lần.

---

## 6. Nhật ký đổi hướng (chỉ ghi khi HƯỚNG đổi)

| Ngày | Đổi gì |
|---|---|
| 2026-08-06 | Lập NORTH-STAR. Chốt tầm nhìn **master_qa = hệ đa-agent** (orchestrator + specialists). Khởi động **pentest agent** (specialist #10) — black-box, standalone, giai đoạn 1. Rename `threease_qa → master_qa` HOÀN TẤT (dir/docs/remote/registry + GitHub repo + push, commit ed717ee). |
| 2026-08-10 | **Mũi nhọn lỗ đầu tiên LẬT: IDOR → auth/session (P1).** Phương án B (thiếu `TESTSEED002`) thành đường CHÍNH. Pentest đi **design → build → live**: lớp **P1 đóng trọn** (P1a access + P1b refresh + continuity gate), chạy thật `stg-monomana` **2× CONFIRMED**. IDOR lùi thành P2 (chờ data). Merged vào `qa-brain`. |
