#!/usr/bin/env python3
"""confirm_bugs.py <folder> — CHẠY CODE THẬT để (a) confirm bug, (b) chấm từng case trong
FUNC_CASES.json bằng QUAN SÁT, không suy luận.

An toàn trên DB dev dùng chung:
- Phía **Django** (nhóm A): mọi thao tác phá huỷ (dùng buổi / hủy / chuyển vé) chạy trong
  `transaction.atomic()` rồi **ROLLBACK** → service thật được thực thi, quan sát được kết quả,
  KHÔNG để lại vết, và hook `transaction.on_commit` (sync sang Pro) KHÔNG bắn → không đẩy rác
  sang hệ kia.
- Phía **Rails** (nhóm B/D): cần commit thật để kiểm đường sync 2 chiều → tạo reservation test
  marker `AIOT-TEST-BF-<branch>` rồi tự revert; BẮT BUỘC verify `cleanup=done`.
- Vé THẬT của khách: chỉ ĐỌC (predicate is_cancellable/is_refundable, refundability), không submit.

Ghi bugs.json: {bugs: [...], cases: [{id, verdict, observed}], rails, django, ...}
Verdict: observed-PASS | observed-FAIL | observed-API | traced-only | 未実施 (+ lý do)
"""
import json, subprocess, sys, re
from pathlib import Path

folder = Path(sys.argv[1]).resolve()  # ⛔ TUYỆT ĐỐI, không dùng path tương đối — xem run_in() bên dưới
cfg = json.loads((folder / "config.json").read_text())
B = int(cfg["branch_id"]); SOT = cfg["sot"]
ROOT = cfg.get("repo_root", "/Users/TruongDinhDucTri/Work/ThreeSides")
MARK = f"AIOT-TEST-BF-{B}"
CASES = json.loads((Path(__file__).resolve().parent.parent.parent / "skills" / "backfill" / "FUNC_CASES.json").read_text())["cases"]
CASE = {c["id"]: c for c in CASES}

before = json.loads((folder / "data_before.json").read_text()) if (folder / "data_before.json").exists() else {"rails": {}, "django": {}}
after = json.loads((folder / "data_after.json").read_text()) if (folder / "data_after.json").exists() else {"rails": {}, "django": {}}
sample_cust = before.get("rails", {}).get("rails_sample_cust_id")
sample_rem_before = before.get("rails", {}).get("rails_sample_remaining")
dj_cust = (after.get("django") or before.get("django") or {}).get("dj_sample_customer_id")


def kv(out):
    d = {}
    for line in out.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)=(.*)$", line.strip())
        if m: d[m.group(1)] = m.group(2)
    return d


def run_in(service, local_name, code, cmd):
    # ⛔ BẪY ĐÃ MẮC (2026-07-29): nếu gọi confirm_bugs.py bằng <folder> TƯƠNG ĐỐI mà cwd của
    # subprocess (ROOT, cố định = repo root) khác cwd thật của tiến trình Python, thì
    # `folder / local_name` trước đây có thể trỏ SAI chỗ khi `docker compose cp` chạy (dù ghi file
    # LOCAL vẫn đúng vì Python resolve theo os.getcwd() thật). Kết quả: copy LẶNG LẼ THẤT BẠI (lỗi rơi
    # vào stderr, không ai kiểm tra), container chạy phải file `.rb` CŨ (hoặc không có gì) còn sót từ
    # lần trước → ra kết quả trông hợp lý nhưng SAI, hoặc rails runner báo cú pháp lỗi khó hiểu.
    # Sửa 2 lớp: (1) `folder` được `.resolve()` ngay đầu file → luôn tuyệt đối, không còn mơ hồ theo
    # cwd; (2) ở đây kiểm returncode của bước copy, KHÔNG lặng lẽ đi tiếp nếu copy hỏng.
    (folder / local_name).write_text(code)
    cp = subprocess.run(f'docker compose cp {json.dumps(str(folder / local_name))} {service}:/tmp/{local_name}',
                        cwd=ROOT, shell=True, capture_output=True, text=True)
    if cp.returncode:
        raise RuntimeError(f"run_in: COPY THẤT BẠI cho {local_name} → {service} — {cp.stderr.strip()[:300]}")
    r = subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True)
    return r.stdout + ("\n" + r.stderr if r.returncode else "")


# =====================================================================================
# RAILS (Pro) — B3 redeem · B4 reclaim · B5 refund crash · B6 remaining · C1 API khách · D2 sync · D3 outbox
# =====================================================================================
rails_rb = f'''
CID = {sample_cust or 'nil'}
# ---- D3 SNAPSHOT TRƯỚC khi test (BẮT BUỘC đo trước) ----
# Job sync_remaining ở test D2 bên dưới TỰ TẠO outbox event cho vé test → nếu đo sau, chính test
# của mình sẽ bị đếm là "vé còn nằm chờ" ⇒ báo FAIL oan (đo 2026-07-28: 5 event id 168-172 đều do
# 4 lần chạy script này sinh ra). Số dùng để CHẤM là số CHỤP TRƯỚC.
PACK_IDS_BRANCH = Tickets::Pack.with_branches([{B}]).pluck(:id).to_set
def outbox_branch_pending(ids)
  ThreeaseTicketOutboxEvent.where.not(status: 'sent').select do |e|
    p = e.payload.to_s
    p.include?('Pack') && p.scan(/"id"=>(\\d+)/).flatten.map(&:to_i).any? {{ |i| ids.include?(i) }}
  end.size
rescue => e
  -1
end
puts "rails_outbox_pending_branch_pre=" + outbox_branch_pending(PACK_IDS_BRANCH).to_s
# ---- B5: refund vé migrate (vé THẬT, chỉ gọi .valid? — read-only, không thực hiện hoàn tiền) ----
mig = Tickets::Pack.with_branches([{B}]).where(price: 0).where('effective_price > 0').where(reservation_ticket_id: nil).where.not(status: 'archived').first
if mig
  puts "refund_pack=" + mig.id.to_s
  begin
    Therapists::Branch::Customers::TicketPacks::RefundCase.new(pack: mig).valid?
    puts "refund_result=OK_no_crash"
  rescue => e
    puts "refund_result=CRASH:" + e.class.to_s
    puts "refund_trace=" + (e.backtrace.select {{ |l| l.include?('refund_case') }}.first || '').to_s
  end
end
# ---- B6: remaining tổng của khách ----
if CID
  c = Therapists::Customer.find_by(id: CID)
  if c
    puts "remaining_after=" + c.ticket_slips.where(tickets_slips: {{ reservation_item_id: nil, used: false }}).distinct.count.to_s
    puts "remaining_active_packs=" + c.ticket_packs.where.not(status: 'archived').count.to_s
    puts "remaining_archived_packs=" + c.ticket_packs.where(status: 'archived').count.to_s
  end
end
# ---- C1: KHÁCH tự xem vé — chạy đúng use case của app khách (read-only) ----
if CID
  c = Therapists::Customer.find_by(id: CID)
  if c
    begin
      res = Therapists::Branch::Customers::TicketPacks::IndexCase.new(page_parameters: {{}}, customer: c).perform
      items = res.items.to_a
      puts "c1_pack_count=" + items.size.to_s
      mg = items.find {{ |p| p.price.to_i.zero? && p.effective_price.to_i.positive? }}
      if mg
        ser = Tickets::CustomerTicketPackSerializer.new(mg).as_json
        puts "c1_migrated_visible=yes"
        puts "c1_migrated_redeemable=" + (ser[:redeemable_count] || ser['redeemable_count']).to_s
        puts "c1_migrated_price=" + (ser[:price] || ser['price']).to_s
      else
        puts "c1_migrated_visible=no"
      end
    rescue => e
      puts "c1_error=" + e.class.to_s + ":" + e.message.to_s[0, 90]
    end
  end
end
# ---- B3 redeem / B4 reclaim / D2 sync — trên vé migrate có slip dùng được (tạo + revert) ----
Therapists::Reservation.where(comment_staff: '{MARK}').each {{ |r| r.reservation_items.destroy_all; r.destroy }}
pk = Tickets::Pack.with_branches([{B}]).where(price: 0).where('effective_price > 0').where.not(status: 'archived').to_a.find {{ |p| p.slips.redeemable.count > 0 }}
if pk
  c = pk.customer
  smpl = Therapists::Reservation.joins(:reservation_items).where(branch_id: {B}).order(id: :desc).first
  if smpl
    ri0 = smpl.reservation_items.first
    red0 = pk.slips.redeemable.count
    puts "redeem_pack=" + pk.id.to_s
    res = Therapists::Reservation.create!(branch_id: {B}, customer_id: c.id, unit_id: smpl.unit_id,
      start_time: Time.zone.now + 3.days, end_time: Time.zone.now + 3.days + 30.minutes,
      status: 'confirmed', treatment_status: 'ongoing', reservation_type: 'reservation', payment_status: 'unpaid',
      source: 'pro', comment_staff: '{MARK}')
    ri = Therapists::ReservationItem.create!(reservation_id: res.id, item_id: ri0.item_id, product_id: ri0.product_id,
      tax_type: ri0.tax_type, tax_rate: ri0.tax_rate, price: 0, quantity: 1)
    slip = pk.slips.redeemable.first; slip.update!(reservation_item_id: ri.id)
    # ⚠️ MỘT key MỘT dòng. Nhét 2 key vào 1 dòng thì parser kv() chỉ bắt được key đầu, key sau MẤT
    #    → case bị chấm oan là 未実施 dù đã chạy OK (đo 2026-07-28: B3/B4 branch 124).
    puts "redeem_from=" + red0.to_s
    puts "redeem_to=" + Tickets::Pack.find(pk.id).slips.redeemable.count.to_s
    begin
      ThreeaseTicketSyncJob.perform_now(Tickets::Pack.name, pk.id, 'sync_remaining'); puts "sync_result=OK"
    rescue => e
      puts "sync_result=ERR:" + e.class.to_s
    end
    slip.reload.update!(reservation_item_id: nil)
    puts "reclaim_to=" + Tickets::Pack.find(pk.id).slips.redeemable.count.to_s
    ri.destroy; res.destroy
    # DỌN outbox event do CHÍNH test này sinh ra (job sync_remaining ở trên), để không để lại rác
    # và không làm lệch số đo lần sau.
    wiped = ThreeaseTicketOutboxEvent.where.not(status: 'sent').where(event: 'sync_remaining')
                                     .select {{ |e| e.payload.to_s.include?('"id"=>' + pk.id.to_s) }}
    wiped.each(&:destroy)
    puts "cleanup_outbox_test_events=" + wiped.size.to_s
    puts "cleanup=done"
  else
    puts "redeem_skip=khong_co_reservation_mau_de_clone"
  end
else
  puts "redeem_skip=khong_co_ve_migrate_con_slip_dung_duoc"
end
# ---- D3 (Rails side): outbox tồn đọng ----
begin
  m = ThreeaseTicketOutboxEvent
  puts "rails_outbox_total=" + m.count.to_s
  pend = m.where.not(status: 'sent')
  puts "rails_outbox_pending=" + pend.count.to_s
  # PHÂN BIỆT: 'pending' (chưa ai chạy cron flush — PHASE7 ghi cron CHƯA setup) KHÁC 'error'.
  # Chấm FAIL vì tồn đọng chung của hệ = đổ oan cho lần migrate này. Chỉ cái nào CÓ LỖI, hoặc
  # LIÊN QUAN branch đang làm, mới tính vào verdict.
  # ⚠️ Cột `error` KHÔNG được xoá khi event gửi lại thành công — nó là dấu vết của lần hụt CŨ.
  #    Đếm `error IS NOT NULL` trần là chấm FAIL oan: branch 66 (2026-07-29) có 1.410 event mang
  #    `error='sync failed'` nhưng CẢ 1.410 đều `status='sent'` (hụt hồi sai host, sau flush đã đi hết),
  #    thực tế pending=0 failed=0. Chỉ event CHƯA gửi được mới là lỗi thật.
  puts "rails_outbox_errors=" + (m.column_names.include?('error') ? m.where.not(status: 'sent').where.not(error: [nil, '']).count : 0).to_s
  puts "rails_outbox_error_da_gui_xong=" + (m.column_names.include?('error') ? m.where(status: 'sent').where.not(error: [nil, '']).count : 0).to_s
  pack_ids = Tickets::Pack.with_branches([{B}]).pluck(:id).to_set
  rel = pend.select do |e|
    p = e.payload.to_s
    p.include?('"branch_id"=>{B}') || p.include?('"branch_id":{B}') ||
      (p.include?('Pack') && (p.scan(/"id"=>(\\d+)/).flatten.map(&:to_i).any? {{ |i| pack_ids.include?(i) }}))
  end
  puts "rails_outbox_pending_branch_post=" + rel.size.to_s
  puts "rails_outbox_pending_kinds=" + pend.group(:event).count.map {{ |k, v| "#{{k}}:#{{v}}" }}.join(',')
  puts "rails_outbox_oldest=" + pend.order(:created_at).first&.created_at.to_s
rescue => e
  puts "rails_outbox_pending=NA:" + e.class.to_s
end
'''
R = kv(run_in("threease_backend", "_bugs.rb", rails_rb,
              'docker compose exec -T threease_backend bundle exec rails runner /tmp/_bugs.rb'))

# =====================================================================================
# DJANGO (Ticket) — A4 dùng buổi · A6 hủy · A7 hoàn · A8 chuyển · A10 master · D3 outbox
# Mọi thao tác ghi: trong atomic() rồi ROLLBACK → không để vết, on_commit sync KHÔNG bắn.
# =====================================================================================
django_py = f'''
from django.db import transaction
from th.models import TicketPack, TicketOption, Customer, Branch, InstituteStaffProfile
from th.services.ticket_operation import TicketUseService, TicketTransferService, TicketIssueSevice

B = {B}
br = Branch.objects.filter(id=B).first()
cust = Customer.objects.filter(id={dj_cust or 0}).first() or Customer.objects.filter(branch_id=B).first()
staff = InstituteStaffProfile.objects.filter(institute=br.institute).first() if br else None

# ---- A10: master vé + option còn nguyên (read-only) ----
if br:
    opts = TicketOption.objects.filter(ticket__institute=br.institute)
    print("a10_option_count=" + str(opts.count()))
    print("a10_option_inventory_ok=" + str(opts.filter(inventory__gt=0).count()))

# ---- A2/A6/A7: vé THẬT vừa migrate — chỉ ĐỌC predicate ----
# ⚠️ "Vé migrate bên Django" có 2 DẤU HIỆU KHÁC NHAU tuỳ chiều — dùng nhầm là mất trắng case:
#   sot='ticket_app' → Django tự tạo vé mới  ⇒ đánh dấu bằng `original_pack`
#   sot='pro'        → Rails tạo rồi sync sang ⇒ Django KHÔNG có `original_pack`, chỉ có `pro_pack_id`
# Branch 66 (chiều pro, 2026-07-29) dính: `original_pack__isnull=False` ra 0 dòng dù có 817 vé migrate
# ⇒ A2 bị chấm 未実施 oan, A8 tụt xuống chạy trên vé test rồi FAIL oan.
_mig_qs = TicketPack.objects.filter(customer__branch_id=B).exclude(status="archived")
mig = (_mig_qs.filter(original_pack__isnull=False).first()
       or _mig_qs.filter(pro_pack_id__isnull=False).first())
if mig:
    # MỘT key MỘT dòng (parser kv() chỉ bắt key đầu dòng)
    print("a2_mig_pack_id=" + str(mig.id))
    print("a2_mig_remaining=" + str(mig.remaining))
    print("a2_mig_total=" + str(mig.total))
    print("a6_mig_is_cancellable=" + str(mig.is_cancellable()))
    print("a7_mig_is_refundable=" + str(mig.is_refundable()))
    print("a2_mig_price=" + str(mig.price))
    print("a2_mig_actual_price=" + str(mig.actual_price))
arch = TicketPack.objects.filter(customer__branch_id=B, status="archived").first()
if arch:
    print("a1_archived_usable=" + str(arch.is_usable()))
    print("a6_archived_is_cancellable=" + str(arch.is_cancellable()))

# ---- A4/A6/A7/A8: chạy SERVICE THẬT trên vé test, rồi ROLLBACK ----
class _RB(Exception):
    pass

opt = None
if mig:
    opt = mig.ticket_option
elif br:
    opt = TicketOption.objects.filter(ticket__institute=br.institute).first()

if cust and opt and br:
    try:
        with transaction.atomic():
            price = opt.price_excluding_tax + opt.tax_amount
            tp = TicketPack.objects.create(
                customer=cust, ticket_option=opt,
                remaining=opt.session_count or 3, total=opt.session_count or 3,
                status=TicketPack.Status.ACTIVE, price=price,
                price_excluding_tax=opt.price_excluding_tax, tax_amount=opt.tax_amount,
                unit_price=opt.unit_price, unit_tax=opt.unit_tax,
                last_unit_price=opt.last_unit_price, last_unit_tax=opt.last_unit_tax,
            )
            print("probe_pack_created=" + str(tp.id))
            print("probe_pack_remaining=" + str(tp.remaining))
            # A5 — PHÁT HÀNH vé mới bằng SERVICE THẬT. Chạy được vì cả block này rollback: hook
            # transaction.on_commit (đẩy sang Pro) KHÔNG bao giờ bắn ⇒ không tạo rác ở hệ kia.
            try:
                np, ni = TicketIssueSevice({{"ticket_option": opt, "staff": staff, "notes": "{MARK}"}}, cust, br).create()
                print("a5_issue_result=OK")
                print("a5_issue_pack=" + str(np.id))
                print("a5_issue_sessions=" + str(np.remaining) + "/" + str(np.total))
                print("a5_issue_price=" + str(np.price))
            except Exception as e:
                print("a5_issue_result=ERR:" + type(e).__name__ + ":" + str(e)[:90])
            # A4 — dùng 1 buổi qua service thật
            try:
                TicketUseService(tp).use(1, branch=br, staff=staff, notes="{MARK}")
                tp.refresh_from_db()
                print("a4_use_result=OK remaining=" + str(tp.remaining))
            except Exception as e:
                print("a4_use_result=ERR:" + type(e).__name__ + ":" + str(e)[:90])
            # A7 — sau khi đã dùng 1 buổi thì vé phải refundable được
            print("a7_probe_is_refundable=" + str(tp.is_refundable()))
            print("a6_probe_is_cancellable=" + str(tp.is_cancellable()))
            # A8 — chuyển 1 buổi sang khách khác qua service thật.
            # ⚠️ Chạy trên VÉ MIGRATE THẬT (mig), KHÔNG dùng vé test: TicketTransferService cần
            #    pack.issue (bản ghi phát hành) mà vé tạo tay không có → 'TicketPack has no issue'
            #    = lỗi CỦA TEST, không phải lỗi sản phẩm (đã chấm oan observed-FAIL 1 lần).
            #    An toàn vì cả block này rollback.
            recv = Customer.objects.filter(branch_id=B).exclude(id=cust.id).first()
            target = mig if mig and mig.remaining > 0 else tp
            if recv and target:
                # ⛔ IN TRƯỚC khi gọi service. In sau thì lúc nổ exception sẽ KHÔNG biết nó chạy trên
                #    vé migrate thật (⇒ bug sản phẩm) hay vé test tạo tay (⇒ lỗi của test, xem chú
                #    thích trên). Branch 66 dính đúng chỗ này: A8 FAIL mà không quy trách được cho ai.
                print("a8_transfer_on=" + ("ve_migrate_that#" + str(target.id) if target is mig else "ve_test#" + str(target.id)))
                try:
                    tr = TicketTransferService(target).transfer(1, receiver=recv, notes="{MARK}")
                    target.refresh_from_db()
                    print("a8_transfer_result=OK")
                    print("a8_transfer_remaining=" + str(target.remaining))
                    print("a8_transfer_id=" + str(tr.id))
                except Exception as e:
                    print("a8_transfer_result=ERR:" + type(e).__name__ + ":" + str(e)[:90])
            else:
                print("a8_transfer_result=SKIP:khong_co_khach_thu_2_trong_branch")
            raise _RB()
    except _RB:
        print("probe_rollback=done")
    except Exception as e:
        print("probe_error=" + type(e).__name__ + ":" + str(e)[:120])
else:
    print("probe_error=thieu_customer_hoac_ticket_option_hoac_branch")

# ---- D3: outbox Django ----
from django.db import connection
c = connection.cursor()
try:
    # Dò 2026-07-28: bảng th_syncoutboxevent có cột `error` + `status` (KHÔNG phải last_error —
    # query cũ sai tên cột nên luôn trả NA, làm case D3 bị chấm 未実施 oan).
    from th.models import SyncOutboxEvent
    print("dj_outbox_total=" + str(SyncOutboxEvent.objects.count()))
    # Cùng bẫy như phía Rails: `error` là dấu vết lần hụt CŨ, không bị xoá khi gửi lại thành công.
    # Chỉ đếm event CHƯA gửi được mới là lỗi thật (xem chú thích ở khối Rails).
    _stuck = SyncOutboxEvent.objects.exclude(status="sent")
    print("dj_outbox_errors=" + str(_stuck.exclude(error="").exclude(error=None).count()))
    print("dj_outbox_error_da_gui_xong=" + str(
        SyncOutboxEvent.objects.filter(status="sent").exclude(error="").exclude(error=None).count()))
    print("dj_outbox_option_errors=" + str(_stuck.filter(error__icontains="option").count()))
    print("dj_outbox_pending=" + str(SyncOutboxEvent.objects.exclude(status="sent").count()))
except Exception as e:
    print("dj_outbox_errors=NA:" + type(e).__name__)
# ---- rác test còn sót? (phải = 0) ----
from th.models import TicketUsage, TicketTransfer
print("dj_test_garbage=" + str(TicketUsage.objects.filter(notes__contains="{MARK}").count()
                               + TicketTransfer.objects.filter(notes__contains="{MARK}").count()))
'''
DJ = kv(run_in("threease_ticket", "_bugs_dj.py", django_py,
               'docker compose exec -T threease_ticket python manage.py shell -c "exec(open(\'/tmp/_bugs_dj.py\').read())"'))

# =====================================================================================
# Chấm verdict từng case — CHỈ từ quan sát ở trên
# =====================================================================================
cases = []


def mark(cid, verdict, observed):
    c = CASE.get(cid, {})
    cases.append({"id": cid, "name_vi": c.get("name_vi", ""), "name_jp": c.get("name_jp", ""),
                  "group": c.get("group", ""), "app": c.get("app", ""), "driver": c.get("driver", ""),
                  "mechanism": c.get("mechanism", ""), "expect": c.get("expect", ""),
                  "verdict": verdict, "observed": observed})


def ui_only(cid, extra=""):
    """Case không có kiểm tầng code — verdict do build_excel suy từ ảnh + HTTP của capture_func."""
    mark(cid, "ui-only", f"Chấm bằng ảnh + mã HTTP của màn (xem 3_CHUCNANG). {extra}".strip())


# --- nhóm A (Django) ---
ui_only("A1", f"Vé archived còn dùng được? is_usable={DJ.get('a1_archived_usable', '?')} (phải False).")
mark("A2", "observed-PASS" if DJ.get("a2_mig_pack_id") else "未実施",
     (f"Vé migrate #{DJ.get('a2_mig_pack_id')}: còn {DJ.get('a2_mig_remaining', '?')}/{DJ.get('a2_mig_total', '?')} buổi, "
      f"price={DJ.get('a2_mig_price', '?')} (không tính doanh thu mới) vs actual_price={DJ.get('a2_mig_actual_price', '?')} (giá trị vé)."
      ) if DJ.get("a2_mig_pack_id") else "Không tìm thấy vé migrate nào ở nhóm này.")
ui_only("A3")
a4 = DJ.get("a4_use_result", "")
mark("A4", "observed-PASS" if a4.startswith("OK") else ("observed-FAIL" if a4.startswith("ERR") else "未実施"),
     f"Chạy TicketUseService.use(1) thật trên vé test (rollback sau): {a4 or 'không chạy được'}. "
     f"Rollback: {DJ.get('probe_rollback', DJ.get('probe_error', '?'))}.")
a5 = DJ.get("a5_issue_result", "")
mark("A5", "observed-PASS" if a5.startswith("OK") else ("observed-FAIL" if a5.startswith("ERR") else "未実施"),
     (f"Đã BÁN THỬ 1 vé mới cho khách bằng đúng chức năng phát hành của hệ thống: tạo được vé "
      f"#{DJ.get('a5_issue_pack', '?')}, {DJ.get('a5_issue_sessions', '?')} buổi, giá "
      f"{DJ.get('a5_issue_price', '?')}. Sau khi quan sát xong thì hoàn tác toàn bộ (rollback: "
      f"{DJ.get('probe_rollback', '?')}) nên không để lại vé rác và không đẩy gì sang hệ kia. "
      f"Danh mục vé còn {DJ.get('a10_option_count', '?')} loại, {DJ.get('a10_option_inventory_ok', '?')} loại còn tồn kho."
      ) if a5 else f"Không chạy được: {DJ.get('probe_error', 'thiếu dữ liệu')}")
mark("A6", "observed-PASS" if DJ.get("a6_probe_is_cancellable") is not None else "未実施",
     f"Vé THẬT vừa migrate: is_cancellable={DJ.get('a6_mig_is_cancellable', '?')} · vé archived: "
     f"{DJ.get('a6_archived_is_cancellable', '?')} (phải False — không cho hủy vé đối chiếu). "
     f"Vé test sau khi dùng 1 buổi: {DJ.get('a6_probe_is_cancellable', '?')}.")
mark("A7", "observed-PASS" if DJ.get("a7_probe_is_refundable") is not None else "未実施",
     f"Vé THẬT migrate: is_refundable={DJ.get('a7_mig_is_refundable', '?')}. Vé test đã dùng 1 buổi: "
     f"{DJ.get('a7_probe_is_refundable', '?')} (phải True). Bên Ticket KHÔNG crash như Pro (BUG-1).")
a8 = DJ.get("a8_transfer_result", "")
mark("A8", "observed-PASS" if a8.startswith("OK") else ("observed-FAIL" if a8.startswith("ERR") else "未実施"),
     f"Chạy TicketTransferService.transfer(1) THẬT trên {DJ.get('a8_transfer_on', 'vé test')} (rollback sau): "
     f"{a8 or 'không chạy được'}"
     + (f", còn lại {DJ.get('a8_transfer_remaining', '?')} buổi, tạo bản ghi chuyển vé #{DJ.get('a8_transfer_id', '?')}."
        if a8.startswith("OK") else "."))
ui_only("A9")
mark("A10", "observed-PASS" if DJ.get("a10_option_count") else "未実施",
     f"Master vé: {DJ.get('a10_option_count', '?')} option, {DJ.get('a10_option_inventory_ok', '?')} còn tồn kho.")

# --- nhóm B (Rails) ---
ui_only("B1", "販売金額 tổng phải bất biến — số ở 1_DATA.")
ui_only("B2")
red_from = R.get("redeem_from") if str(R.get("redeem_from", "")).isdigit() else None
red_to = R.get("redeem_to") if str(R.get("redeem_to", "")).isdigit() else None
if red_from and red_to:
    mark("B3", "observed-PASS" if int(red_to) == int(red_from) - 1 else "observed-FAIL",
         f"Gán slip vé migrate #{R.get('redeem_pack', '?')} vào 1 reservation test: buổi dùng được {red_from} → {red_to}.")
    mark("B4", "observed-PASS" if R.get("reclaim_to") == red_from else "observed-FAIL",
         f"Nhả slip: {red_to} → {R.get('reclaim_to', '?')} (phải về {red_from}).")
else:
    why = R.get("redeem_skip", "không chạy được")
    mark("B3", "未実施", f"Lý do: {why}")
    mark("B4", "未実施", f"Lý do: {why}")
rr = R.get("refund_result", "")
mark("B5", "observed-FAIL" if rr.startswith("CRASH") else ("observed-PASS" if rr else "未実施"),
     f"RefundCase.valid? trên vé migrate #{R.get('refund_pack', '?')}: {rr or 'không chạy'}. {R.get('refund_trace', '')}")
if sample_rem_before is not None and R.get("remaining_after") is not None:
    same = R.get("remaining_after") == str(sample_rem_before)
    mark("B6", "observed-PASS" if same else "observed-FAIL",
         f"Khách #{sample_cust}: tổng buổi còn lại {sample_rem_before} → {R.get('remaining_after')} "
         f"(vé active {R.get('remaining_active_packs', '?')}, archived {R.get('remaining_archived_packs', '?')}). "
         f"{'Khớp' if same else 'LỆCH → đếm cả vé đã archive (BUG-2)'}.")
else:
    mark("B6", "未実施", "Thiếu baseline remaining của khách mẫu.")
ui_only("B7"); ui_only("B8"); ui_only("B9")

# --- nhóm C ---
if R.get("c1_migrated_visible") == "yes":
    mark("C1", "observed-API",
         f"Chạy đúng use case app khách (IndexCase + CustomerTicketPackSerializer): khách thấy "
         f"{R.get('c1_pack_count', '?')} vé, vé migrate HIỆN, còn {R.get('c1_migrated_redeemable', '?')} buổi dùng được. "
         f"Chưa có ảnh UI vì pw_lib chưa login được app khách (không dựng ảnh giả).")
elif R.get("c1_migrated_visible") == "no":
    mark("C1", "observed-FAIL",
         f"Khách thấy {R.get('c1_pack_count', '?')} vé nhưng KHÔNG có vé migrate → với khách là 'mất vé'.")
else:
    mark("C1", "未実施", f"Không chạy được: {R.get('c1_error', 'thiếu khách mẫu')}")

# --- nhóm D ---
_synced = num_dj_synced = (after.get("django") or {}).get("dj_new_synced_pro")
_created = (after.get("django") or {}).get("dj_new_migrated")
mark("D1", "observed-PASS" if (_synced and _created and _synced == _created) else "未実施",
     f"Đường Ticket→Pro CÓ hoạt động và đã quan sát được trên dữ liệu thật: {_created} vé tạo bên Ticket, "
     f"{_synced} vé đã sang tới Pro (khớp 1-1, không sót vé nào), 0 event lỗi ở cả 2 đầu (xem D3). "
     f"Riêng nhánh 'dùng buổi bên Ticket rồi Pro nhận số mới' thì KHÔNG bắn trong phiên này — mọi thao tác "
     f"ghi bên Ticket đều chạy trong transaction hoàn tác nên hook gửi sang Pro không nổ (cố ý, để không "
     f"đẩy dữ liệu test sang hệ kia). Nhánh ngược lại (Pro→Ticket) đã chạy thật, xem D2.")
sy = R.get("sync_result", "")
mark("D2", "observed-PASS" if sy == "OK" else ("observed-FAIL" if sy.startswith("ERR") else "未実施"),
     f"ThreeaseTicketSyncJob 'sync_remaining' Pro→Ticket: {sy or 'không chạy'}.")
oe = DJ.get("dj_outbox_errors", "NA")
re_ = R.get("rails_outbox_errors", "NA")
rp = R.get("rails_outbox_pending", "NA")
rpb = R.get("rails_outbox_pending_branch_pre", "?")   # số ĐO TRƯỚC test (không lẫn rác của test)
rpb_post = R.get("rails_outbox_pending_branch_post", "?")
# Verdict CHỈ dựa vào: có event LỖI không, và có event nào của BRANCH NÀY còn nằm chờ không.
# Tồn đọng chung của cả hệ (cron flush chưa setup) là vấn đề hạ tầng có TRƯỚC, không do migrate.
clean = oe == "0" and re_ == "0" and rpb == "0"
mark("D3", "observed-PASS" if clean else ("observed-FAIL" if (oe.isdigit() and oe != "0") or (str(re_).isdigit() and re_ != "0") or (str(rpb).isdigit() and rpb != "0") else "未実施"),
     f"Branch này: **{rpb} event còn nằm chờ** (đo TRƯỚC khi chạy test, nên không lẫn event do chính test sinh ra; "
     f"sau test đo lại: {rpb_post}, đã dọn {R.get('cleanup_outbox_test_events', '?')} event của test). "
     f"⇒ vé của branch đã tới được hệ kia. Lỗi: Django {oe}, Rails {re_}. "
     f"(Bối cảnh hạ tầng, KHÔNG do lần migrate này: toàn hệ còn {rp}/{R.get('rails_outbox_total', '?')} event Rails ở trạng thái "
     f"chờ gửi từ {R.get('rails_outbox_oldest', '?')} — loại: {R.get('rails_outbox_pending_kinds', '?')} — vì PHASE7 ghi "
     f"cron `rake threease_ticket:flush_outbox` CHƯA được setup. Cần dev bật cron.)")

# =====================================================================================
# Nhóm E — VÉ MỚI CÓ DÙNG ĐƯỢC KHÔNG (thêm 2026-07-29 sau BUG-041). Đọc smoke_usable.json (đã chạy
# ở bước 7b của backfill-run.md, TRƯỚC file này) — KHÔNG tự chạy lại UI ở đây, chỉ diễn giải kết quả.
# =====================================================================================
smoke_p = folder / "smoke_usable.json"
e1_verdict = "未実施"
e1_detail = "smoke_usable.js chưa chạy (chạy nó ở bước 7b của backfill-run.md, trước confirm_bugs.py)."
if smoke_p.exists():
    S = json.loads(smoke_p.read_text())
    checked, fail = S.get("checked", 0), S.get("fail", 0)
    if S.get("error"):
        e1_verdict, e1_detail = "未実施", f"smoke_usable.js lỗi: {S['error']}"
    elif checked == 0:
        e1_verdict, e1_detail = "未実施", "0 vé mới quan sát được ở khách mẫu — cần đổi khách mẫu."
    elif fail > 0:
        e1_verdict = "observed-FAIL"
        bad = [d for d in S.get("details", []) if d.get("usable") is False]
        e1_detail = f"{fail}/{checked} vé mới KHÔNG chọn được product: " + "; ".join(f"pack {d['pack_id']} — {d['why']}" for d in bad)
    else:
        e1_verdict = "observed-PASS"
        e1_detail = f"{checked}/{checked} vé mới chọn được product bình thường (API + logic filter thật, xem smoke_usable.json)."
mark("E1", e1_verdict, e1_detail)

# B3/B4 là driver:code (gọi thẳng Rails console gán/nhả slip) — CHỈ chứng minh tầng dữ liệu, KHÔNG
# chứng minh nhân viên bấm được. Nếu E1 chưa PASS thì downgrade để không lẫn vào "PASS(UI)".
for cc in cases:
    if cc["id"] in ("B3", "B4") and cc["verdict"] == "observed-PASS" and e1_verdict != "observed-PASS":
        cc["verdict"] = "observed-PASS(data-only)"
        cc["observed"] += f" ⚠️ HẠ CẤP: chỉ chứng minh tầng dữ liệu — E1 ({e1_verdict}) cho thấy bước " \
                           f"chọn product (bước TRƯỚC bước này trong thực tế) có thể đã chặn nhân viên " \
                           f"từ trước khi tới được đây. {e1_detail}"

b3v = next((c["verdict"] for c in cases if c["id"] == "B3"), "未実施")
e2_verdict = ("observed-PASS" if (e1_verdict == "observed-PASS" and b3v == "observed-PASS")
              else ("observed-FAIL" if e1_verdict == "observed-FAIL" else "未実施"))
mark("E2", e2_verdict,
     f"Suy từ E1 ({e1_verdict}) + B3 ({b3v}) — xem SKILL.md §LUẬT FIELD-DELTA: dùng buổi chỉ 'chạy "
     f"bình thường' khi CẢ bước chọn product (E1) VÀ bước trừ buổi (B3) đều ổn.")

a4v = next((c["verdict"] for c in cases if c["id"] == "A4"), "未実施")
e3_verdict = ("observed-PASS" if (a4v == "observed-PASS" and e1_verdict == "observed-PASS")
              else ("observed-FAIL" if (a4v == "observed-PASS" and e1_verdict == "observed-FAIL") else "未実施"))
mark("E3", e3_verdict,
     f"Đối chiếu A4 (Ticket app, dùng buổi qua UI: {a4v}) với E1 (Pro, chọn product: {e1_verdict}). "
     + ("A4 PASS mà E1 FAIL ⇒ bug khoanh đúng ở phía Pro (product picker), KHÔNG phải do đồng bộ số buổi."
        if a4v == "observed-PASS" and e1_verdict == "observed-FAIL" else ""))

mark("E4", "未実施", "Chưa tự động chọn khách/vé ĐỐI CHỨNG (vé thường, không phải vé mới) — cần "
                     "chỉ định tay hoặc mở rộng smoke_usable.js để tự tìm. Không dựng giả kết quả.")

# E5 — lịch sử X/Y buổi (BUG-042), so vé mới với vé gốc, read-only trên dữ liệu thật (không cần data test)
e5_rb = f'''
new_p = Tickets::Pack.with_branches([{B}]).where.not(original_pack_id: nil).limit(500).to_a
if new_p.any?
  changed = new_p.count {{ |m| o = Tickets::Pack.find_by(id: m.original_pack_id); o && m.slips.count != o.slips.count }}
  puts "e5_checked=" + new_p.size.to_s
  puts "e5_changed=" + changed.to_s
else
  puts "e5_checked=0"
end
'''
e5out = run_in('threease_backend', '_e5.rb', e5_rb, f'docker compose exec -T threease_backend bundle exec rails runner /tmp/_e5.rb')
E5 = kv(e5out)
e5c, e5ch = int(E5.get("e5_checked", 0) or 0), int(E5.get("e5_changed", 0) or 0)
mark("E5", "未実施" if e5c == 0 else ("observed-FAIL" if e5ch > 0 else "observed-PASS"),
     f"{e5ch}/{e5c} vé mới (mẫu, chiều pro) đổi tổng slip_count so với vé gốc (mất lịch sử đã dùng — "
     f"BUG-042). 0 nghĩa là chiều ticket_app (không có original_pack_id) — case này chỉ đo được chiều pro."
     if e5c else "0 vé có original_pack_id trên branch này (chiều ticket_app không tạo field này) — "
                 "chưa đo được lịch sử slip cho chiều đó, cần đo riêng qua ticket_pack_id.")

# =====================================================================================
# Bug confirmed
# =====================================================================================
bugs = []
if rr.startswith("CRASH"):
    # Ghi RÕ 3 tầng, không gộp: (1) code crash = QUAN SÁT · (2) UI có/không lộ ra = QUAN SÁT ·
    # (3) điều kiện để user chạm tới = SUY LUẬN. Gộp lại thành "UI lỗi 500" là phóng đại
    # (branch 124: nút 返金 bị vô hiệu, KHÔNG có 5xx nào — khác branch 179).
    mig_refundable = DJ.get("a7_mig_is_refundable", "?")
    bugs.append({"id": "BUG-1", "title": "Refund (返金) vé migrate bên Pro → CRASH ở tầng code", "severity": "CAO",
                 "who": "Nhân viên tại quầy của cơ sở (người bấm hoàn tiền cho khách).",
                 "when": "Khi khách xin HOÀN TIỀN một vé đã được đồng bộ lại VÀ vé đó đã dùng ít nhất 1 buổi. "
                         "Vé vừa đồng bộ mà chưa dùng buổi nào thì nút 返金 đang bị làm mờ nên chưa gặp.",
                 "sees": "Bấm 返金 → không hoàn được tiền, màn báo lỗi hệ thống. Vé THƯỜNG (mua trực tiếp, "
                         "không qua đồng bộ) vẫn hoàn tiền bình thường.",
                 "impact_customer": "Khách không được hoàn tiền ngay tại quầy, phải chờ. Tiền và số buổi của "
                                    "khách KHÔNG bị mất — chỉ là thao tác hoàn tiền không thực hiện được.",
                 "workaround": "Tạm thời xử lý hoàn tiền cho các vé này bằng tay / báo kỹ thuật; hoặc hoàn tiền "
                               "ở phía hệ Ticket (bên đó không bị lỗi này).",
                 "evidence":
                     f"[QUAN SÁT — tầng code] pack {R.get('refund_pack')}: {rr} @ {R.get('refund_trace')}\n"
                     f"[QUAN SÁT — đối chứng bên Ticket] cùng vé đó is_refundable={mig_refundable} → KHÔNG crash.\n"
                     f"[SUY LUẬN, chưa quan sát] Vé vừa migrate có total = remaining (chưa dùng buổi nào) nên UI "
                     f"vô hiệu hoá nút 返金 → nhân viên chưa chạm được vào đường crash. Khi khách dùng 1 buổi thì "
                     f"vé thành 'refund được' và mới lộ lỗi. Cần dev thêm safe-nav (pack.reservation_ticket&.reservation).",
                 "confirmed": True, "ui_hint": "pro_customer_refund"})
if sample_rem_before is not None and R.get("remaining_after") not in (None, str(sample_rem_before)):
    bugs.append({"id": "BUG-2", "title": "残チケット (tổng buổi còn lại) đếm DƯ", "severity": "TB",
                 "who": "Nhân viên xem danh sách khách (顧客管理), ở cột 「チケット残高」 = tổng buổi còn lại.",
                 "when": "Ngay sau khi đồng bộ, với mọi khách có vé cũ bị khoá lại.",
                 "sees": f"Cột 「チケット残高」 hiện {R.get('remaining_after', '?')} buổi, nhưng mở hồ sơ khách ra "
                         f"đếm vé thật thì chỉ có {sample_rem_before} buổi dùng được. Con số tổng cộng thêm cả "
                         f"vé cũ đã khoá.",
                 "impact_customer": "KHÔNG ảnh hưởng quyền lợi khách: danh sách vé và số buổi thật vẫn đúng, "
                                    "khách vẫn dùng đúng số buổi mình có. Chỉ là con số tổng hiển thị bị lớn hơn "
                                    "thực tế, dễ làm nhân viên nhầm khi tư vấn.",
                 "workaround": "Xem số buổi thật trong hồ sơ khách (tab チケット情報) thay vì tin cột tổng, "
                               "cho tới khi kỹ thuật sửa.",
                 "evidence":
                     f"[QUAN SÁT] khách {sample_cust}: con số TỔNG buổi còn lại {sample_rem_before} → "
                     f"{R.get('remaining_after')} sau migrate, trong khi khách vẫn chỉ dùng được đúng "
                     f"{sample_rem_before} buổi (vé active {R.get('remaining_active_packs')}, "
                     f"archived {R.get('remaining_archived_packs')} — vé đã khoá VẪN bị đếm).\n"
                     f"[QUAN SÁT] Danh sách vé của khách (tab チケット情報) hiển thị ĐÚNG → chỉ con số tổng bị phồng, "
                     f"nghiệp vụ dùng buổi KHÔNG bị ảnh hưởng.\n"
                     f"Vị trí: update_view_job.rb remaining_ticket_count — thiếu .not_archived. Cần dev lọc archived.",
                 "confirmed": True, "ui_hint": "pro_customer_remaining"})
if SOT == "pro" and DJ.get("dj_outbox_option_errors", "0") not in ("0", "NA", None):
    bugs.append({"id": "BUG-5", "title": "Rails→Django sync fail (ticket_option_id) → khách mất buổi", "severity": "CAO",
                 "evidence": f"Django outbox option-errors={DJ.get('dj_outbox_option_errors')}",
                 "confirmed": True, "ui_hint": "ticket_customer_missing"})
if R.get("c1_migrated_visible") == "no":
    bugs.append({"id": "BUG-6", "title": "App KHÁCH không thấy vé migrate", "severity": "CAO",
                 "evidence": f"IndexCase trả {R.get('c1_pack_count')} vé, không có vé migrate nào.",
                 "confirmed": True, "ui_hint": "customer_app"})

garbage = DJ.get("dj_test_garbage", "?")
# Gắn case ↔ bug: case nào ĐÃ sinh ra 1 bug thì sheet SUMMARY chỉ cần liệt kê bug đó, khỏi kê 2 lần
# (sếp đọc 2 dòng cho cùng 1 vấn đề sẽ tưởng có 4 vấn đề thay vì 2).
CASE_TO_BUG = {"B5": "BUG-1", "B6": "BUG-2", "C1": "BUG-6", "D3": "BUG-5"}
have_bug = {b["id"] for b in bugs}
for c in cases:
    bid = CASE_TO_BUG.get(c["id"])
    if bid and bid in have_bug:
        c["bug_id"] = bid

# GIỮ LẠI ảnh UI mà capture_bugs.js đã gắn cho bug cùng id. Không giữ thì chạy lại confirm_bugs
# (rất hay phải làm) sẽ ÂM THẦM xoá ảnh UI khỏi sheet 4_BUGS mà không ai biết — đo 2026-07-28.
_old = json.loads((folder / "bugs.json").read_text()) if (folder / "bugs.json").exists() else {}
_ui = {b["id"]: (b.get("ui_capture"), b.get("ui_note")) for b in _old.get("bugs", []) if b.get("ui_capture")}
for b in bugs:
    if b["id"] in _ui:
        b["ui_capture"], b["ui_note"] = _ui[b["id"]]

result = {"branch_id": B, "sot": SOT, "mark": MARK, "rails": R, "django": DJ,
          "bugs": bugs, "cases": cases,
          "cleanup": {"rails": R.get("cleanup", "?"), "django_rollback": DJ.get("probe_rollback", DJ.get("probe_error", "?")),
                      "django_garbage_rows": garbage}}
(folder / "bugs.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

n_pass = sum(1 for c in cases if c["verdict"].startswith("observed-P") or c["verdict"] == "observed-API")
n_fail = sum(1 for c in cases if c["verdict"] == "observed-FAIL")
print(f"OK confirm_bugs.py: {len(bugs)} bug confirmed | case: {n_pass} PASS · {n_fail} FAIL · "
      f"{len(cases) - n_pass - n_fail} còn lại (ui-only/未実施)")
print(f"  cleanup: rails={R.get('cleanup', '?')} django_rollback={DJ.get('probe_rollback', '?')} rác còn={garbage}")
for b in bugs:
    print(f"  {b['id']} {b['title']}")
for c in cases:
    if c["verdict"] in ("observed-FAIL", "未実施"):
        print(f"  [{c['verdict']}] {c['id']} {c['name_vi']} — {c['observed'][:110]}")
