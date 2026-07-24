#!/usr/bin/env python3
"""confirm_bugs.py <folder> — chạy code THẬT để confirm bug sau migrate (đọc data_before.json).
- BUG refund crash: RefundCase.valid? trên vé migrate (reservation_ticket=nil).
- BUG remaining dư: remaining_ticket_count sample customer before vs after.
- Tầng3 ②③⑤: redeem/reclaim/sync test (tạo reservation AIOT-TEST, cleanup).
- BUG-5 (CHỈ sot=pro): Django outbox sync fail + vé migrate có tới Django không (ticket_option_id).
Ghi bugs.json. Tạo test data có marker AIOT-TEST + tự cleanup.
"""
import json, subprocess, sys, re
from pathlib import Path

folder = Path(sys.argv[1])
cfg = json.loads((folder / "config.json").read_text())
B = int(cfg["branch_id"]); SOT = cfg["sot"]; ROOT = cfg.get("repo_root", "/Users/TruongDinhDucTri/Work/ThreeSides")
before = json.loads((folder / "data_before.json").read_text()) if (folder / "data_before.json").exists() else {"rails": {}}
sample_cust = before.get("rails", {}).get("rails_sample_cust_id")
sample_rem_before = before.get("rails", {}).get("rails_sample_remaining")

def rails(rb):
    (folder / "_bugs.rb").write_text(rb)
    subprocess.run(f'docker compose cp {json.dumps(str(folder / "_bugs.rb"))} threease_backend:/tmp/_bugs.rb', cwd=ROOT, shell=True, capture_output=True, text=True)
    return subprocess.run('docker compose exec -T threease_backend bundle exec rails runner /tmp/_bugs.rb', cwd=ROOT, shell=True, capture_output=True, text=True).stdout

def kv(out):
    d = {}
    for l in out.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)=(.*)$", l.strip())
        if m: d[m.group(1)] = m.group(2)
    return d

# --- Rails: refund crash + remaining + redeem/reclaim/sync (1 lượt) ---
rb = f'''
CID = {sample_cust or 'nil'}
# BUG-1 refund: ve migrate (price=0, eff>0, reservation_ticket nil) trong branch
mig = Tickets::Pack.with_branches([{B}]).where(price:0).where('effective_price>0').where(reservation_ticket_id:nil).where.not(status:'archived').first
if mig
  puts "refund_pack=" + mig.id.to_s
  begin
    Therapists::Branch::Customers::TicketPacks::RefundCase.new(pack: mig).valid?
    puts "refund_result=OK_no_crash"
  rescue => e
    puts "refund_result=CRASH:" + e.class.to_s
    puts "refund_trace=" + (e.backtrace.select{{|l| l.include?('refund_case')}}.first || '').to_s
  end
end
# BUG-2 remaining (neu co sample customer)
if CID
  c = Therapists::Customer.find_by(id: CID)
  if c
    rem = c.ticket_slips.where(tickets_slips:{{reservation_item_id:nil, used:false}}).distinct.count
    puts "remaining_after=" + rem.to_s
    puts "remaining_active_packs=" + c.ticket_packs.where.not(status:'archived').count.to_s
    puts "remaining_archived_packs=" + c.ticket_packs.where(status:'archived').count.to_s
  end
end
# Tang3 redeem/reclaim/sync tren ve migrate co slip redeemable
Therapists::Reservation.where(comment_staff:'AIOT-TEST-BF-{B}').each {{ |r| r.reservation_items.destroy_all; r.destroy }}
pk = Tickets::Pack.with_branches([{B}]).where(price:0).where('effective_price>0').where.not(status:'archived').to_a.find {{ |p| p.slips.redeemable.count > 0 }}
if pk
  c = pk.customer
  smpl = Therapists::Reservation.joins(:reservation_items).where(branch_id:{B}).order(id: :desc).first
  if smpl
    ri0 = smpl.reservation_items.first
    red0 = pk.slips.redeemable.count
    res = Therapists::Reservation.create!(branch_id:{B}, customer_id:c.id, unit_id:smpl.unit_id,
      start_time: Time.zone.parse('2026-07-30 10:00'), end_time: Time.zone.parse('2026-07-30 10:30'),
      status:'confirmed', treatment_status:'ongoing', reservation_type:'reservation', payment_status:'unpaid',
      source:'pro', comment_staff:'AIOT-TEST-BF-{B}')
    ri = Therapists::ReservationItem.create!(reservation_id:res.id, item_id:ri0.item_id, product_id:ri0.product_id,
      tax_type:ri0.tax_type, tax_rate:ri0.tax_rate, price:0, quantity:1)
    slip = pk.slips.redeemable.first; slip.update!(reservation_item_id: ri.id)
    red1 = Tickets::Pack.find(pk.id).slips.redeemable.count
    puts "redeem_from=" + red0.to_s + " redeem_to=" + red1.to_s
    begin; ThreeaseTicketSyncJob.perform_now(Tickets::Pack.name, pk.id, 'sync_remaining'); puts "sync_result=OK"; rescue => e; puts "sync_result=ERR:" + e.class.to_s; end
    slip.reload.update!(reservation_item_id: nil)
    red2 = Tickets::Pack.find(pk.id).slips.redeemable.count
    puts "reclaim_to=" + red2.to_s
    ri.destroy; res.destroy
    puts "cleanup=done"
  end
end
'''
R = kv(rails(rb))

# --- BUG-5 (chỉ Pro→Ticket): Django outbox sync fail + vé tới Django? ---
bug5 = {}
if SOT == "pro":
    dpy = f'''
from th.models import TicketPack
q = TicketPack.objects.filter(customer__branch_id={B})
print("dj_packs_after=" + str(q.count()))
print("dj_migrated_after=" + str(q.filter(original_pack__isnull=False).count()))
from django.db import connection
c = connection.cursor()
try:
    c.execute("SELECT count(*) FROM th_syncoutboxevent WHERE last_error IS NOT NULL AND last_error != ''")
    print("dj_outbox_errors=" + str(c.fetchone()[0]))
    c.execute("SELECT count(*) FROM th_syncoutboxevent WHERE last_error ILIKE '%option%'")
    print("dj_outbox_option_errors=" + str(c.fetchone()[0]))
except Exception as e:
    print("dj_outbox_errors=NA")
'''
    (folder / "_bugs_dj.py").write_text(dpy)
    subprocess.run(f'docker compose cp {json.dumps(str(folder / "_bugs_dj.py"))} threease_ticket:/tmp/_bugs_dj.py', cwd=ROOT, shell=True, capture_output=True, text=True)
    dout = subprocess.run("docker compose exec -T threease_ticket python manage.py shell -c \"exec(open('/tmp/_bugs_dj.py').read())\"", cwd=ROOT, shell=True, capture_output=True, text=True).stdout
    bug5 = kv(dout)

# --- Đóng gói bugs.json ---
bugs = []
if R.get("refund_result", "").startswith("CRASH"):
    bugs.append({"id": "BUG-1", "title": "Refund (返金) vé migrate → CRASH", "severity": "CAO",
                 "evidence": f"pack {R.get('refund_pack')}: {R.get('refund_result')} @ {R.get('refund_trace')}", "confirmed": True})
if sample_rem_before is not None and R.get("remaining_after") is not None and R.get("remaining_after") != str(sample_rem_before):
    bugs.append({"id": "BUG-2", "title": "残チケット (buổi còn lại) đếm DƯ", "severity": "TB",
                 "evidence": f"customer {sample_cust}: remaining {sample_rem_before} → {R.get('remaining_after')} (active {R.get('remaining_active_packs')}, archived {R.get('remaining_archived_packs')})", "confirmed": True})
if SOT == "pro" and bug5.get("dj_outbox_option_errors", "0") not in ("0", "NA", None):
    bugs.append({"id": "BUG-5", "title": "Rails→Django sync fail (ticket_option_id) → khách mất buổi", "severity": "CAO",
                 "evidence": f"Django outbox option-errors={bug5.get('dj_outbox_option_errors')}; migrated tới Django={bug5.get('dj_migrated_after')}", "confirmed": True})

result = {"branch_id": B, "sot": SOT, "rails": R, "bug5": bug5, "bugs": bugs,
          "tier3": {"redeem": f"{R.get('redeem_from')}→{R.get('redeem_to')}", "reclaim": R.get("reclaim_to"),
                    "sync": R.get("sync_result"), "cleanup": R.get("cleanup")}}
(folder / "bugs.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
print(f"OK confirm_bugs.py: {len(bugs)} bug confirmed | redeem {R.get('redeem_from')}→{R.get('redeem_to')} sync={R.get('sync_result')} cleanup={R.get('cleanup')}")
for b in bugs: print(f"  {b['id']} {b['title']}")
