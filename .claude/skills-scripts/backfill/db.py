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
  puts "rails_branch_name=" + br.name.to_s
  puts "rails_institute_id=" + br.institute_id.to_s
  # sample customer co ve mo coi (baseline remaining cho bug remaining)
  s = cand.first
  if s
    c = s.customer
    rem = c.ticket_slips.where(tickets_slips: {{reservation_item_id: nil, used: false}}).distinct.count
    puts "rails_sample_cust_id=" + c.id.to_s
    puts "rails_sample_cust_code=" + c.try(:customer_code).to_s
    puts "rails_sample_remaining=" + rem.to_s
    puts "rails_sample_orphan_pack=" + s.id.to_s
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
'''
(folder / "_db_django.py").write_text(django_py)
sh(f'docker compose cp {json.dumps(str(folder / "_db_django.py"))} threease_ticket:/tmp/_db_django.py')
dout = sh("docker compose exec -T threease_ticket python manage.py shell -c \"exec(open('/tmp/_db_django.py').read())\"")
D = kv(dout)

noop = (R.get("rails_candidates") in (None, "0")) and (D.get("dj_candidates") in (None, "0"))
data = {"phase": phase, "branch_id": B, "sot": cfg["sot"], "noop": noop, "rails": R, "django": D}
(folder / f"data_{phase}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

# ---- DATA_<phase>.md (người đọc) ----
lines = [f"# DATA — {phase.upper()} (branch {B}, sot={cfg['sot']}, {cfg.get('branch_name_jp','')})", ""]
if noop:
    lines.append("> ⚠️ **NO-OP: candidates = 0 cả 2 bên** — branch trống, KHÔNG có gì để migrate.")
lines += [
    "| Bên | candidates (vé mồ côi) | Σ price / buổi | active | all(incl archived) |",
    "|---|---|---|---|---|",
    f"| Django(Ticket) | {D.get('dj_candidates','?')} | buổi {D.get('dj_cand_sessions','?')} | total {D.get('dj_total','?')} ¥{D.get('dj_sum_price','?')} | — |",
    f"| Rails(Pro) | {R.get('rails_candidates','?')} | ¥{R.get('rails_cand_price','?')} / {R.get('rails_cand_sessions','?')} buổi | {R.get('rails_active_count','?')} ¥{R.get('rails_active_price','?')} | {R.get('rails_all_count','?')} ¥{R.get('rails_all_price','?')} |",
]
if phase == "after":
    lines += ["", f"- Rails archived: **{R.get('rails_archived','?')}** · vé synced migrate: **{R.get('rails_synced_migrated','?')}** · Django vé mới synced Pro: **{D.get('dj_new_synced_pro','?')}**",
              f"- **Σprice all-incl-archived (Rails) = ¥{R.get('rails_all_price','?')}** → phải GIỮ NGUYÊN so với before (doanh thu bất biến)."]
if R.get("rails_sample_cust_id"):
    lines += ["", f"- Sample customer (Pro): id={R.get('rails_sample_cust_id')} code={R.get('rails_sample_cust_code')} remaining={R.get('rails_sample_remaining')} (baseline bug remaining)"]
(folder / f"DATA_{phase}.md").write_text("\n".join(lines))
print(f"OK db.py {phase}: noop={noop} | rails_cand={R.get('rails_candidates')} django_cand={D.get('dj_candidates')}")
print(f"  → data_{phase}.json + DATA_{phase}.md")
