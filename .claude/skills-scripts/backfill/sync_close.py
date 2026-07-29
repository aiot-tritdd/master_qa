#!/usr/bin/env python3
"""sync_close.py <folder> [--flush] — ĐÓNG SÓNG SYNC sau migrate. Chạy NGAY sau migrate.js.

VÌ SAO CÓ FILE NÀY (đo thật 2026-07-29, branch 66 gerbill):
  migrate.js báo "DONE", `candidates = 0` cả 2 bên, doanh thu bất biến — **mọi chỉ số đều xanh**,
  nhưng **354/817 vé mới vẫn chưa sang Django** (`ticket_pack_id` NULL). Khách mở app sẽ KHÔNG thấy vé.
  Không có bước nào trong pipeline bắt được chuyện đó, vì `candidates=0` chỉ nói "đã migrate",
  KHÔNG nói "đã sync". Hai chuyện khác nhau.

  Vé rớt lại vì sync là job nền (Rails `queue_adapter=async`, hàng đợi nằm TRONG RAM tiến trình Puma):
  restart backend = **mất sạch hàng đợi**, không có gì chạy lại giúp. Chỗ cứu duy nhất là outbox.

CHẠY MẶC ĐỊNH = CHỈ ĐỌC (báo cáo). Có `--flush` mới thật sự flush outbox.

⚠️ `MAX_RETRIES = 5`: mỗi lần flush hụt thì `retry_count` +1, chạm 5 là event chết vĩnh viễn
   (`status='failed'`, các lần flush sau bỏ qua). Nên script CHẶN flush khi thấy `retry_count >= 3`
   hoặc đã có event `failed` — lúc đó phải đi sửa nguyên nhân (thường là sai host: xem
   `zz_local_dev_ticket_host.rb`) chứ không phải flush thêm.
"""
import json
import subprocess
import sys
import re
from pathlib import Path

folder = Path(sys.argv[1])
DO_FLUSH = "--flush" in sys.argv
cfg = json.loads((folder / "config.json").read_text())
B = int(cfg["branch_id"])
ROOT = cfg.get("repo_root", "/Users/TruongDinhDucTri/Work/ThreeSides")


def sh(cmd):
    return subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True).stdout


def kv(out):
    d = {}
    for line in out.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)=(.*)$", line.strip())
        if m:
            d[m.group(1)] = m.group(2)
    return d


PROBE = f'''
n = Tickets::Pack.with_branches([{B}]).where.not(original_pack_id: nil)
puts "new_packs=" + n.count.to_s
puts "synced=" + n.where.not(ticket_pack_id: nil).count.to_s
puts "not_synced=" + n.where(ticket_pack_id: nil).count.to_s
o = ThreeaseTicketOutboxEvent
puts "pending=" + o.where(status: "pending").count.to_s
puts "failed=" + o.where(status: "failed").count.to_s
puts "max_retry=" + (o.where(status: "pending").maximum(:retry_count) || 0).to_s
'''


def probe():
    """Chạy script Ruby qua FILE (giống db.py). Truyền script thẳng trên dòng lệnh hay vỡ vì
    quoting nhiều tầng shell→docker→ruby; khi vỡ thì `rails runner` im lặng không in gì."""
    p = folder / "_sync_probe.rb"
    p.write_text(PROBE)
    sh(f'docker compose cp {json.dumps(str(p))} threease_backend:/tmp/_sync_probe.rb')
    d = kv(sh("docker compose exec -T threease_backend bundle exec rails runner /tmp/_sync_probe.rb"))
    # ⛔ Probe rỗng thì MỌI con số là None → `int(... or 0)` = 0 → script sẽ in "✅ không còn gì phải
    #    đóng" trong khi thực tế CHƯA ĐO ĐƯỢC GÌ. Đúng loại pass-giả nguy hiểm nhất. Phải nổ.
    if "new_packs" not in d:
        sys.exit("LỖI: probe không trả về gì (rails runner hỏng?) — KHÔNG kết luận được, dừng.")
    return d


before = probe()
print(f"TRƯỚC: vé mới={before.get('new_packs')} · đã sync={before.get('synced')} · "
      f"CHƯA sync={before.get('not_synced')} | outbox pending={before.get('pending')} "
      f"failed={before.get('failed')} max_retry={before.get('max_retry')}")

need = int(before.get("not_synced") or 0)
pending = int(before.get("pending") or 0)
failed = int(before.get("failed") or 0)
max_retry = int(before.get("max_retry") or 0)

after = before
if need == 0 and pending == 0:
    print("✅ Không còn gì phải đóng: mọi vé mới đã sang Django, outbox rỗng.")
elif not DO_FLUSH:
    print(f"⚠️  CẦN FLUSH: {need} vé chưa sang Django, {pending} event đang chờ.")
    print("    Chạy lại với --flush (hoặc báo user quyết). KHÔNG flush mù.")
elif failed > 0 or max_retry >= 3:
    # Đây là chốt cứu event, không phải sự thận trọng thừa: flush tiếp chỉ đẩy retry_count tới 5 rồi chết hẳn.
    print(f"⛔ CHẶN FLUSH: failed={failed}, max_retry={max_retry} (trần MAX_RETRIES=5).")
    print("    Sửa nguyên nhân trước — thường là sai host Rails→Django")
    print("    (`threease_backend/config/initializers/zz_local_dev_ticket_host.rb` phải trỏ http://ticket:8000).")
    sys.exit(2)
else:
    print(f"→ flush outbox ({pending} event)…")
    # Gọi qua `rails runner` chứ KHÔNG `docker compose restart` / `rake` ngoài tiến trình:
    # hàng đợi async nằm trong RAM Puma, restart là mất sạch job chưa chạy.
    fp = folder / "_sync_flush.rb"
    fp.write_text('require "rake"\nRails.application.load_tasks\n'
                  'Rake::Task["threease_ticket:flush_outbox"].invoke\n')
    sh(f'docker compose cp {json.dumps(str(fp))} threease_backend:/tmp/_sync_flush.rb')
    out = sh("docker compose exec -T threease_backend bundle exec rails runner /tmp/_sync_flush.rb")
    print(out.strip()[-1500:])
    after = probe()
    print(f"SAU  : vé mới={after.get('new_packs')} · đã sync={after.get('synced')} · "
          f"CHƯA sync={after.get('not_synced')} | outbox pending={after.get('pending')} "
          f"failed={after.get('failed')}")
    if int(after.get("not_synced") or 0) > 0:
        print("⚠️  VẪN CÒN vé chưa sang Django — KHÔNG được báo 'xong'. Soi `error` trong outbox.")

res = {"branch_id": B, "before": before, "after": after, "flushed": DO_FLUSH}
(folder / "sync_close.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
print(f"  → {folder}/sync_close.json")
