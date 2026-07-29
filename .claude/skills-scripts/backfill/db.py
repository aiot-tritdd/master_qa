#!/usr/bin/env python3
"""db.py <folder> <before|after> — query Django+Rails cho branch trong config.json.
Chạy trên HOST, shell sang docker (Rails runner + Django shell), gộp → data_<phase>.json + DATA_<phase>.md.
KHÔNG hardcode branch. CHỈ ĐỌC DB (read-only) — an toàn chạy bất cứ lúc nào.
"""
import json, subprocess, sys, re
from pathlib import Path

folder = Path(sys.argv[1]); phase = sys.argv[2] if len(sys.argv) > 2 else "before"
cfg = json.loads((folder / "config.json").read_text())
B = int(cfg["branch_id"]); ROOT = cfg.get("repo_root", "/Users/TruongDinhDucTri/Work/ThreeSides")

# Khách mẫu: phase after PHẢI dùng lại ĐÚNG khách của phase before, nếu không ảnh/số trước-sau là của
# 2 người khác nhau ⇒ không so được (và sau migrate thì candidates=0 nên không chọn được khách mới).
PIN_CUST = None
_pb = folder / "data_before.json"
if phase == "after" and _pb.exists():
    PIN_CUST = (json.loads(_pb.read_text()).get("rails") or {}).get("rails_sample_cust_id")

def sh(cmd):
    return subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True).stdout

def kv(out):
    d = {}
    for line in out.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)=(.*)$", line.strip())
        if m: d[m.group(1)] = m.group(2)
    return d

# ---- RAILS (Pro) ----
rails_rb = f'''
br = Therapists::Branch.find_by(id: {B})
if br.nil?; puts "ERR=branch_not_found"; else
  cand = Tickets::PackMigrationService.candidates_for(br).to_a
  puts "rails_candidates=" + cand.size.to_s
  puts "rails_cand_price=" + cand.sum {{ |p| p.price || 0 }}.to_s
  puts "rails_cand_sessions=" + cand.sum {{ |p| p.redeemable_count || 0 }}.to_s
  allp = Tickets::Pack.with_branches([{B}])
  act = allp.where.not(status: 'archived')
  puts "rails_active_count=" + act.count.to_s
  puts "rails_active_price=" + act.sum(:price).to_s
  puts "rails_all_count=" + allp.count.to_s
  puts "rails_all_price=" + allp.sum(:price).to_s
  puts "rails_archived=" + allp.where(status: 'archived').count.to_s
  synced = allp.where(price: 0).where('effective_price > 0').where.not(ticket_pack_id: nil)
  puts "rails_synced_migrated=" + synced.count.to_s
  # ⛔ "migrate xong" ≠ "sync xong". candidates=0 chỉ nói vé cũ đã được thay; nó KHÔNG nói vé mới
  #    đã sang Django hay chưa. Branch 66 (2026-07-29): candidates=0, doanh thu bất biến, mọi chỉ số
  #    xanh — mà 354/817 vé mới vẫn ticket_pack_id NULL ⇒ khách mở app KHÔNG thấy vé.
  #    Sync là job nền trong RAM Puma: restart backend là mất hàng đợi, không tự chạy lại.
  newp = allp.where.not(original_pack_id: nil)
  puts "rails_new_packs=" + newp.count.to_s
  puts "rails_new_not_synced=" + newp.where(ticket_pack_id: nil).count.to_s
  # trùng do bấm migrate chồng lô (chiều sot=pro, xem SKILL.md): mỗi vé gốc chỉ được 1 vé mới
  puts "rails_new_distinct_original=" + newp.distinct.count(:original_pack_id).to_s
  puts "rails_branch_name=" + br.name.to_s
  puts "rails_institute_id=" + br.institute_id.to_s
  # sample customer co ve mo coi (baseline remaining cho bug remaining).
  # UU TIEN khach CO customer_code — man 顧客管理 ben Pro tim khach bang code, khach khong co code
  # thi capture_func/capture_bugs khong mo duoc man => mat anh B2/B5/B6.
  pinned = {PIN_CUST or 'nil'}
  s = cand.find {{ |p| p.customer&.customer_code.present? }} || cand.first
  c = pinned ? Therapists::Customer.find_by(id: pinned) : s&.customer
  # sau migrate ko còn candidate → lấy khách của 1 vé MIGRATE (price=0, effective_price>0)
  c ||= Tickets::Pack.with_branches([{B}]).where(price: 0).where('effective_price > 0').where.not(status: 'archived').first&.customer
  if c
    puts "rails_sample_cust_name=" + c.try(:name).to_s
    rem = c.ticket_slips.where(tickets_slips: {{reservation_item_id: nil, used: false}}).distinct.count
    # ⚠️ `rem` ở trên đếm CẢ slip của vé đã archived (đúng bằng cách app tính → chính là BUG-2).
    #    Sau migrate vé cũ bị archive nhưng slip vẫn còn ⇒ con số PHỒNG (branch 66: 15 → 30) và ai
    #    đọc cũng tưởng khách được cộng khống. Muốn so trước/sau cho công bằng phải dùng bản
    #    CHỈ-VÉ-ACTIVE dưới đây (branch 66: 15 → 15, đúng bằng nhau).
    rem_act = Tickets::Slip.where(pack_id: c.ticket_packs.where.not(status: 'archived').select(:id),
                                  used: false, reservation_item_id: nil).distinct.count
    puts "rails_sample_remaining_active=" + rem_act.to_s
    puts "rails_sample_cust_id=" + c.id.to_s
    puts "rails_sample_cust_code=" + c.try(:customer_code).to_s
    puts "rails_sample_remaining=" + rem.to_s
    puts "rails_sample_orphan_pack=" + s.id.to_s if s
    puts "rails_sample_active_packs=" + c.ticket_packs.where.not(status: 'archived').count.to_s
    puts "rails_sample_archived_packs=" + c.ticket_packs.where(status: 'archived').count.to_s
  end
end
'''
rout = sh(f'docker compose exec -T threease_backend bundle exec rails runner {json.dumps("-")} <<\'RB\'\n{rails_rb}\nRB')
# rails runner - reads script from stdin; fallback via file if empty
if "rails_candidates=" not in rout:
    (folder / "_db_rails.rb").write_text(rails_rb)
    sh(f'docker compose cp {json.dumps(str(folder / "_db_rails.rb"))} threease_backend:/tmp/_db_rails.rb')
    rout = sh('docker compose exec -T threease_backend bundle exec rails runner /tmp/_db_rails.rb')
R = kv(rout)

# ---- DJANGO (Ticket) ----
django_py = f'''
from th.services.ticket_pack_migration import migration_candidates
from th.models import TicketPack
from django.db.models import Sum
cand = list(migration_candidates({B}))
print("dj_candidates=" + str(len(cand)))
print("dj_cand_sessions=" + str(sum(p.remaining for p in cand)))
b = TicketPack.objects.filter(customer__branch_id={B})
print("dj_total=" + str(b.count()))
print("dj_sum_price=" + str(b.aggregate(s=Sum("price"))["s"] or 0))
newp = b.filter(original_pack__isnull=False)
print("dj_new_migrated=" + str(newp.count()))
print("dj_new_price0=" + str(newp.filter(price=0).count()))
print("dj_new_synced_pro=" + str(newp.exclude(pro_pack_id__isnull=True).count()))
# --- sample id cho FUNC_CASES (capture_func.js dung de mo dung man) ---
sc = cand[0].customer if cand else (b.first().customer if b.exists() else None)
if sc:
    print("dj_sample_customer_id=" + str(sc.id))
    print("dj_sample_customer_name=" + str(getattr(sc, "name", "") or ""))
sp = newp.filter(status="active").first() or b.filter(status="active").first() or b.first()
if sp:
    print("dj_sample_pack_id=" + str(sp.id))
    print("dj_sample_pack_remaining=" + str(sp.remaining))
    print("dj_sample_pack_status=" + str(sp.status))
# Ticket (master) khong co branch_id — lay qua ticket_option cua pack mau
if sp and sp.ticket_option_id:
    print("dj_sample_ticket_id=" + str(sp.ticket_option.ticket_id))
    print("dj_sample_ticket_option_id=" + str(sp.ticket_option_id))
print("dj_archived=" + str(b.filter(status="archived").count()))
'''
(folder / "_db_django.py").write_text(django_py)
sh(f'docker compose cp {json.dumps(str(folder / "_db_django.py"))} threease_ticket:/tmp/_db_django.py')
dout = sh("docker compose exec -T threease_ticket python manage.py shell -c \"exec(open('/tmp/_db_django.py').read())\"")
D = kv(dout)

# candidates = 0 hai bên có 2 NGHĨA KHÁC NHAU tuỳ phase:
#   before → branch TRỐNG, không có gì để migrate (noop thật)
#   after  → ĐÃ MIGRATE XONG HẾT (thành công!) — gọi là noop thì sheet SUMMARY sẽ báo sếp
#            "branch không có gì để đồng bộ", sai hoàn toàn bản chất. Đo 2026-07-28 branch 124.
zero_both = (R.get("rails_candidates") in (None, "0")) and (D.get("dj_candidates") in (None, "0"))
noop = zero_both if phase == "before" else False
data = {"phase": phase, "branch_id": B, "sot": cfg["sot"], "noop": noop,
        "all_done": zero_both if phase == "after" else None, "rails": R, "django": D}
(folder / f"data_{phase}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

# ---- DATA_<phase>.md (người đọc) ----
lines = [f"# DATA — {phase.upper()} (branch {B}, sot={cfg['sot']}, {cfg.get('branch_name_jp','')})", ""]
if noop:
    lines.append("> ⚠️ **NO-OP: candidates = 0 cả 2 bên** — branch trống, KHÔNG có gì để migrate.")
elif phase == "after" and zero_both:
    lines.append("> ✅ **ĐÃ MIGRATE XONG HẾT: candidates = 0 cả 2 bên** — không còn vé mồ côi nào.")
lines += [
    "| Bên | candidates (vé mồ côi) | Σ price / buổi | active | all(incl archived) |",
    "|---|---|---|---|---|",
    f"| Django(Ticket) | {D.get('dj_candidates','?')} | buổi {D.get('dj_cand_sessions','?')} | total {D.get('dj_total','?')} ¥{D.get('dj_sum_price','?')} | — |",
    f"| Rails(Pro) | {R.get('rails_candidates','?')} | ¥{R.get('rails_cand_price','?')} / {R.get('rails_cand_sessions','?')} buổi | {R.get('rails_active_count','?')} ¥{R.get('rails_active_price','?')} | {R.get('rails_all_count','?')} ¥{R.get('rails_all_price','?')} |",
]
if phase == "after":
    lines += ["", f"- Rails archived: **{R.get('rails_archived','?')}** · vé synced migrate: **{R.get('rails_synced_migrated','?')}** · Django vé mới synced Pro: **{D.get('dj_new_synced_pro','?')}**",
              f"- **Σprice all-incl-archived (Rails) = ¥{R.get('rails_all_price','?')}** → phải GIỮ NGUYÊN so với before (doanh thu bất biến)."]
    # 2 cảnh báo này in RA MẶT, không chôn trong json: cả 2 đều từng lọt qua ở branch 66 vì
    # mọi chỉ số khác đều xanh.
    _new = int(R.get("rails_new_packs") or 0)
    _uns = int(R.get("rails_new_not_synced") or 0)
    _dis = int(R.get("rails_new_distinct_original") or 0)
    if _uns:
        lines += ["", f"> 🔴 **CHƯA XONG: {_uns}/{_new} vé mới CHƯA sang Django** (`ticket_pack_id` NULL)."
                      " Khách mở app sẽ không thấy vé. Chạy `sync_close.py <folder> --flush` rồi đo lại."
                      " **KHÔNG được báo 'migrate xong'.**"]
    elif _new:
        lines.append(f"- Sync đã đóng: **{_new}/{_new}** vé mới đã sang Django ✅")
    if _new and _dis and _new != _dis:
        lines += ["", f"> 🔴 **VÉ TRÙNG: {_new} vé mới nhưng chỉ {_dis} vé gốc** (thừa {_new - _dis})."
                      " Nguyên nhân: bấm migrate chồng lô ở chiều `sot=pro` (xem SKILL.md)."
                      " Dọn: giữ `min(id)` mỗi `original_pack_id`, `destroy` phần dư."]
if R.get("rails_sample_cust_id"):
    lines += ["", f"- Sample customer (Pro): id={R.get('rails_sample_cust_id')} code={R.get('rails_sample_cust_code')} remaining={R.get('rails_sample_remaining')} (baseline bug remaining)"]
(folder / f"DATA_{phase}.md").write_text("\n".join(lines))
print(f"OK db.py {phase}: noop={noop} | rails_cand={R.get('rails_candidates')} django_cand={D.get('dj_candidates')}")
print(f"  → data_{phase}.json + DATA_{phase}.md")
