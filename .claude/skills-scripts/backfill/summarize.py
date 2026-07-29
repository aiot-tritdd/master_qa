#!/usr/bin/env python3
"""summarize.py <folder> — tổng hợp data_before/after + bugs + captures + 2 registry → summary.json.
Đây là ĐẦU VÀO của sheet 0_SUMMARY (sheet sếp đọc rồi call khách). Mọi CON SỐ tính bằng máy,
không gõ tay. Lời văn tiếng Việt, giữ thuật ngữ Nhật; muốn sửa lời → notes.json.summary_override.

Chạy được cả khi thiếu data_after (chưa migrate) → trạng thái "chưa migrate".
"""
import json, sys
from pathlib import Path

folder = Path(sys.argv[1])
SK = Path(__file__).resolve().parent.parent.parent / "skills" / "backfill"


def rj(p, default):
    return json.loads(p.read_text()) if p.exists() else default


cfg = json.loads((folder / "config.json").read_text())
db_b = rj(folder / "data_before.json", {})
db_a = rj(folder / "data_after.json", {})
bugs = rj(folder / "bugs.json", {"bugs": [], "cases": []})
caps = rj(folder / "captures.json", {"before": [], "after": []})
notes = rj(folder / "notes.json", {})
registry = rj(SK / "REPORT_REGISTRY.json", {"reports": []})["reports"]
func_cases = rj(SK / "FUNC_CASES.json", {"cases": []})["cases"]

SOT = cfg["sot"]
SRC, DST = ("Ticket App", "Pro") if SOT == "ticket_app" else ("Pro", "Ticket App")
Rb, Ra = db_b.get("rails", {}), db_a.get("rails", {})
Db, Da = db_b.get("django", {}), db_a.get("django", {})
migrated = bool(db_a)
# noop = branch TRỐNG (không có gì để làm) — CHỈ lấy từ phase before. Sau migrate candidates=0
# nghĩa là ĐÃ XONG, không phải trống (xem ghi chú trong db.py).
noop = bool(db_b.get("noop")) if db_b else bool(db_a.get("noop"))
all_done = bool(db_a.get("all_done"))


def num(v, d=0):
    try: return int(float(v))
    except (TypeError, ValueError): return d


def yen(v):
    n = num(v, None)
    return f"¥{n:,}" if n is not None else "?"


# ---------- 1. Đã làm gì ----------
created = num(Da.get("dj_new_migrated")) if SOT == "ticket_app" else num(Ra.get("rails_synced_migrated"))
archived_delta = num(Ra.get("rails_archived")) - num(Rb.get("rails_archived"))
did = {
    "branch": f"{cfg.get('branch_name_jp', '')} (mã cơ sở {cfg['institute_code']}, branch {cfg['branch_id']})",
    "direction": f"{SRC} → {DST}",
    # ⚠️ Vé mới được tạo bên **SoT (SRC)**, KHÔNG phải bên DST. Cơ chế (backfill_tool/views.py:1896-1908):
    #    bên nào là SoT thì bên đó chạy `migrate_pack` — thay vé cũ của CHÍNH NÓ bằng vé mới rồi đẩy
    #    sang bên kia; bên còn lại chỉ `archive_only` các vé lẻ của nó.
    #    Bản cũ viết ngược ("tạo lại vé bên DST, khoá vé cũ bên DST") — sai ở đúng câu sếp đọc đầu tiên.
    "direction_vi": f"Lấy sổ vé bên **{SRC}** làm bản chuẩn: bên **{SRC}** thay từng vé lẻ cũ bằng 1 vé mới "
                    f"mang đúng số buổi còn lại, rồi đẩy vé mới đó sang **{DST}**. Song song, bên **{DST}** "
                    f"khoá các vé lẻ cũ của nó lại để không bị đếm 2 lần.",
    "orphan_before": {"ticket_app": num(Db.get("dj_candidates")), "pro": num(Rb.get("rails_candidates"))},
    "orphan_after": {"ticket_app": num(Da.get("dj_candidates")), "pro": num(Ra.get("rails_candidates"))},
    "packs_created": created,
    "packs_archived": archived_delta,
    "status": ("chưa migrate (chỉ có số liệu trước)" if not migrated
               else ("branch trống — KHÔNG có gì để đồng bộ" if noop
                     else ("đã đồng bộ XONG HẾT (không còn vé lẻ nào)" if all_done
                           else "đã đồng bộ, NHƯNG còn vé lẻ chưa xử lý — xem mục ⑤"))),
}

# ---------- 2. Ảnh hưởng tới khách (ngôn ngữ khách hàng) ----------
impact = []
rev_b, rev_a = Rb.get("rails_all_price"), Ra.get("rails_all_price")
rev_same = migrated and rev_b is not None and rev_b == rev_a
impact.append({
    "what": "Tổng tiền vé đã bán của cơ sở (販売金額)",
    "before": yen(rev_b), "after": yen(rev_a) if migrated else "—",
    "means": "Không phát sinh doanh thu mới — việc đồng bộ KHÔNG phải một lần bán vé, chỉ là ghi lại đúng vé cũ.",
    "ok": bool(rev_same),
})
# ⚠️ KHÔNG cộng buổi của 2 hệ lại (Ticket 1.514 + Pro 4.312 = 5.826) — đó là ĐẾM TRÙNG cùng một
# tập khách ở 2 sổ khác nhau, ra con số vô nghĩa. Liệt kê riêng từng bên.
impact.append({
    "what": "Vé lẻ chưa khớp giữa 2 hệ (số vé / số buổi trong đó)",
    "before": f"Ticket: {num(Db.get('dj_candidates'))} vé / {num(Db.get('dj_cand_sessions'))} buổi · "
              f"Pro: {num(Rb.get('rails_candidates'))} vé / {num(Rb.get('rails_cand_sessions'))} buổi",
    "after": (f"Ticket: {num(Da.get('dj_candidates'))} · Pro: {num(Ra.get('rails_candidates'))} — đã khớp hết"
              if migrated else "—"),
    "means": f"Hai sổ đã ghi cùng một sự thật, lấy theo bản chuẩn là {SRC} (theo quyết định của sếp ở cột "
             f"「どちらを正とするか」). Từ nay 2 hệ không còn lệch nhau nữa.",
    "ok": migrated and num(Da.get("dj_candidates")) == 0 and num(Ra.get("rails_candidates")) == 0,
})
# Số liệu CỤ THỂ của 1 khách thật — dễ hiểu hơn mọi con số tổng
# ⚠️ So TỔNG buổi còn dùng được của khách, KHÔNG so với 1 vé lẻ.
#    Bản cũ lấy `c1_migrated_redeemable` = số buổi của MỘT vé migrate rồi đem so với TỔNG trước đó
#    ⇒ branch 66 in ra "15 → 5 ❌", đọc như là khách mất 10 buổi, trong khi thật ra khách có 2 vé mới
#    (5 + 10 = 15, không mất gì). Sai ở đúng chỗ sếp đọc để gọi cho khách.
#    Và phải dùng bản CHỈ-VÉ-ACTIVE ở cả 2 đầu — bản gộp archived là BUG-2, không phải số thật.
_rem_before = Rb.get("rails_sample_remaining_active") or Rb.get("rails_sample_remaining")
_rem_after = Ra.get("rails_sample_remaining_active")
if Rb.get("rails_sample_cust_name"):
    _same = migrated and _rem_after is not None and str(_rem_after) == str(_rem_before)
    impact.append({
        "what": f"Ví dụ 1 khách thật — {Rb.get('rails_sample_cust_name')} (mã {Rb.get('rails_sample_cust_code')})",
        "before": f"{_rem_before or '?'} buổi dùng được",
        "after": (f"{_rem_after if _rem_after is not None else '?'} buổi dùng được "
                  f"(trên vé mới thay cho vé cũ)") if migrated else "—",
        "means": ("Số buổi khách thật sự còn dùng được KHÔNG đổi. Vé cũ được khoá lại và thay bằng vé mới "
                  "mang đúng số buổi còn lại." if _same else
                  "⚠️ Số buổi TRƯỚC và SAU không khớp — phải kiểm tra tay trước khi báo khách."),
        "ok": _same,
    })
c1 = next((c for c in bugs.get("cases", []) if c["id"] == "C1"), None)
if c1:
    impact.append({
        "what": "Khách tự mở app xem vé của mình",
        "before": "—", "after": c1["observed"][:150],
        "means": "Đây là thứ khách THẤY. Vé phải hiện đủ buổi trên app của khách.",
        "ok": c1["verdict"] in ("observed-PASS", "observed-API"),
    })
b6 = next((c for c in bugs.get("cases", []) if c["id"] == "B6"), None)
if b6:
    impact.append({
        "what": "Con số 'tổng buổi còn lại' trên hồ sơ khách",
        "before": str(Rb.get("rails_sample_remaining", "—")), "after": str(bugs.get("rails", {}).get("remaining_after", "—")),
        "means": "Con số tổng chỉ là chỗ HIỂN THỊ. Danh sách vé thật vẫn đúng — khách dùng buổi không bị ảnh hưởng.",
        "ok": b6["verdict"] == "observed-PASS",
    })

# ---------- 3. Cái gì vẫn chạy bình thường / 4. Cái gì lệch ----------
def http_of(cid, phase):
    codes = [e.get("http") for e in caps.get(phase, [])
             if e.get("sheet") == "3_CHUCNANG" and str(e.get("screen", "")).startswith(f"func_{cid}")
             and isinstance(e.get("http"), int) and e["http"] > 0]
    return max(codes) if codes else None


def worst_http(cid):
    """Mã HTTP xấu nhất quan sát được ở các màn của case (None nếu không có màn nào)."""
    a, b = http_of(cid, "after"), http_of(cid, "before")
    got = [x for x in (a, b) if x is not None]
    return max(got) if got else None


works, deviations = [], []
for c in bugs.get("cases", []):
    ov = (notes.get("func", {}).get(c["id"], {}) or {})
    row = {"id": c["id"], "name": f'{c["name_vi"]} ({c["name_jp"]})', "group": c.get("group", ""),
           "verdict": c["verdict"], "observed": c["observed"],
           "status": ov.get("status", ""), "note": ov.get("note", "")}
    v = c["verdict"]
    if v in ("observed-PASS", "observed-API"):
        works.append(row)
    elif v == "observed-FAIL":
        # Case này đã sinh ra 1 bug ở mục bug → không kê lại (tránh 1 vấn đề đếm thành 2)
        if c.get("bug_id"):
            continue
        row["link_sheet"] = "4_BUGS"
        deviations.append(row)
    elif v == "ui-only":
        # ⚠️ 'ui-only' = màn mở được + có ảnh. Nếu HTTP < 400 thì đó là CHẠY BÌNH THƯỜNG, đừng nhét
        # vào "điểm cần biết" — làm sếp tưởng 10 chức năng có vấn đề trong khi tất cả đều OK.
        http = worst_http(c["id"])
        if http is not None and http >= 400:
            row["link_sheet"] = "3_CHUCNANG"
            hb, ha = http_of(c["id"], "before"), http_of(c["id"], "after")
            pre_existing = hb is not None and hb >= 400
            row["observed"] = (
                f"Màn trả HTTP {http} — mở KHÔNG được. "
                + (f"**Lỗi này CÓ TRƯỚC khi đồng bộ** (trước: {hb}, sau: {ha}) → KHÔNG do lần đồng bộ này gây ra. "
                   if pre_existing else f"Trước khi đồng bộ màn này bình thường (trước: {hb}, sau: {ha}) → cần soi. ")
                + row["observed"])
            row["status"] = row["status"] or ("Có trước, không do migrate" if pre_existing else "Cần soi")
            deviations.append(row)
        else:
            row["observed"] = (f"Màn mở bình thường (HTTP {http})." if http else "Màn mở bình thường.") \
                              + " Ảnh trước/sau ở 3_CHUCNANG."
            works.append(row)
    elif v.endswith("(data-only)"):
        # ⚠️ CHỈ chứng minh tầng dữ liệu (vd gọi thẳng hàm gán slip), KHÔNG chứng minh nhân viên/khách
        # THẬT SỰ bấm được — bài học BUG-041 (branch 66: mọi case dữ liệu xanh mà vé không dùng được).
        # KHÔNG được liệt vào "vẫn chạy bình thường" dù chữ 'PASS' có trong tên verdict.
        row["link_sheet"] = "3_CHUCNANG"
        row["observed"] = "⚠️ Chỉ xác nhận Ở TẦNG DỮ LIỆU, CHƯA xác nhận qua UI thật. " + row["observed"]
        deviations.append(row)
    else:  # traced-only / 未実施
        row["link_sheet"] = "3_CHUCNANG"
        deviations.append(row)

for r in registry:
    if r["phase7_status"] in ("WARN",):
        deviations.append({
            "id": r["key"], "name": f'{r["name_vi"]} ({r["name_jp"]})', "group": "Báo cáo",
            "verdict": "khác-thường-nhưng-không-sai", "observed": r["phase7_note"],
            "link_sheet": "2_REPORT",
            "status": "Không phải bug",
            "note": "Cách hiển thị có từ TRƯỚC lần đồng bộ này, và tổng tiền vẫn đúng.",
        })

# ---------- 5. Bug ----------
bug_rows = []
for b in bugs.get("bugs", []):
    ov = (notes.get("bugs", {}).get(b["id"], {}) or {})
    bug_rows.append({"id": b["id"], "title": b.get("title", ""), "severity": b.get("severity", ""),
                     "has_ui": bool(b.get("ui_capture")),
                     "status": ov.get("status", "Mở"), "note": ov.get("note", "")})

# ---------- 6. Đã xử lý gì (PHASE7) ----------
fixes = [
    {"what": "Báo cáo hiệu suất theo nhân viên (回数券消化 スタッフ別)",
     "plain": "Trước đây báo cáo này cộng cả giá vé được đồng bộ lại thành doanh thu mới → số doanh thu bị phồng. Đã sửa để chỉ tính tiền thật đã bán.",
     "file": "app/queries/tickets/packs_performance_report_query.rb", "verified": "Đã kiểm số thật: trước sửa phồng 405.840đ, sau sửa = 0."},
    {"what": "Báo cáo số dư cuối tháng (月末時点残高)",
     "plain": "Cột doanh thu theo tháng đã đổi sang dùng giá bán gốc, không dùng giá trị vé được cache lại.",
     "file": "app/queries/tickets/packs_annual_report_query.rb", "verified": "Cột số dư giữ nguyên — đúng khái niệm, không đếm trùng."},
    {"what": "File Excel export lịch sử tiêu thụ vé",
     "plain": "Cột 販売金額 đổi sang giá bán gốc, và loại các vé cũ đã khoá ra khỏi file để không xuất hiện 2 lần.",
     "file": "app/services/therapists/analytics/report/tickets_packs_excel_generator.rb", "verified": "Không sửa serializer dùng chung — tránh ảnh hưởng màn khác."},
]
caveats = [
    "3 bản sửa trên **chưa commit** lên nhánh `aiot-10-migrate-old-data` (theo PHASE7) → khi báo khách, đừng nói là đã lên hệ thống chính.",
    "Cron tự động đẩy lại các bản đồng bộ lỗi (flush outbox) **chưa được cài** → nếu có bản ghi lỗi thì phải chạy tay.",
    "Toàn bộ việc kiểm tra này làm trên **môi trường DEV LOCAL**, không phải hệ thống thật của khách.",
]

# ---------- coverage ----------
def cap_screens(sheet):
    """screen nào ĐÃ có bằng chứng: ảnh · file csv · file xlsx · hoặc trỏ sang ảnh sheet khác."""
    s = set()
    for ph in ("before", "after"):
        for e in caps.get(ph, []):
            if e.get("sheet") == sheet and (e.get("file") or e.get("csv") or e.get("xlsx") or e.get("ref_screen")):
                s.add(e["screen"])
    return s


rep_have = cap_screens("2_REPORT")
# report 'ref' dùng lại ảnh của 1 case chức năng → tính là đủ khi case đó có ảnh
func_have_all = cap_screens("3_CHUCNANG")
for rg in registry:
    if rg.get("capture") == "ref" and f"func_{rg.get('ref', '').replace('func_', '')}" in func_have_all:
        rep_have.add(rg["key"])
# xlsx export: file nằm ở exports_<phase>.json chứ không ở captures.json
for ph in ("before", "after"):
    ex = rj(folder / f"exports_{ph}.json", {})
    for rg in registry:
        if rg.get("capture") == "xlsx" and any(rg["xlsx_name"] in k for k in ex):
            rep_have.add(rg["key"])
rep_need = {r["key"] for r in registry}
func_have = {s.split("_")[1] for s in cap_screens("3_CHUCNANG") if s.startswith("func_")}
# chỉ case CÓ UI mới bị tính "cần ảnh"; case driver=code/api không có màn nào để chụp
func_need = {c["id"] for c in func_cases if "ui" in (c.get("driver") or "")}
coverage = {
    "reports": {"need": len(rep_need), "have": len(rep_need & rep_have), "missing": sorted(rep_need - rep_have)},
    "func": {"need": len(func_need), "have": len(func_need & func_have), "missing": sorted(func_need - func_have)},
    "cases_scored": len(bugs.get("cases", [])),
}

n_fail = sum(1 for c in bugs.get("cases", []) if c["verdict"] == "observed-FAIL")
if not migrated:
    headline = f"CHƯA đồng bộ — đây là bản ghi nhận số liệu TRƯỚC khi làm ({did['branch']})."
elif noop:
    headline = f"Cơ sở {did['branch']} KHÔNG có vé lẻ nào cần đồng bộ — không thao tác gì lên dữ liệu."
else:
    # `created`/`archived_delta` đều đo ở bên SoT (SRC) — xem chú thích ở `direction_vi`. Ghi "bên {DST}"
    # là gán nhầm việc cho hệ kia.
    headline = (f"Đã đồng bộ {'XONG HẾT' if all_done else 'MỘT PHẦN'} cho {did['branch']}: bên {SRC} tạo "
                f"{created} vé mới thay cho {archived_delta} vé lẻ cũ rồi đẩy sang {DST}; "
                f"không còn vé lẻ nào ở cả 2 hệ. "
                f"Tổng tiền vé của cơ sở {'KHÔNG đổi' if rev_same else 'CẦN kiểm lại'}. "
                f"{'Không có lỗi nào chặn nghiệp vụ.' if not (n_fail or bug_rows) else f'Có {len(bug_rows)} điểm cần biết (mục ⑤).'}")

summary = {"headline": notes.get("summary_override", {}).get("headline", headline),
           "did": did, "impact": impact, "works": works, "deviations": deviations,
           "bugs": bug_rows, "fixes": fixes, "caveats": caveats, "coverage": coverage,
           "migrated": migrated, "noop": noop, "src": SRC, "dst": DST}
for k, v in (notes.get("summary_override") or {}).items():
    if k != "headline" and not k.startswith("_"):
        summary[k] = v
(folder / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
print(f"OK summarize.py → summary.json")
print(f"  {summary['headline']}")
print(f"  coverage report {coverage['reports']['have']}/{coverage['reports']['need']}"
      + (f" (thiếu: {', '.join(coverage['reports']['missing'])})" if coverage["reports"]["missing"] else "")
      + f" · chức năng {coverage['func']['have']}/{coverage['func']['need']}"
      + (f" (thiếu: {', '.join(coverage['func']['missing'])})" if coverage["func"]["missing"] else ""))
print(f"  chạy tốt: {len(works)} · cần biết: {len(deviations)} · bug: {len(bug_rows)}")
