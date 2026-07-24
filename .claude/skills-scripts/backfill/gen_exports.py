#!/usr/bin/env python3
"""gen_exports.py <folder> — sinh 3 file xlsx report Pro đã-fix (history/performance/annual)
cho branch trong config, filter branch_ids. Chạy generator THẲNG qua Rails console (khỏi đánh vật
async UI). Cần initializer zz_local_dev_storage.rb (ép :local). Lưu vào after/ + đọc tổng vào exports.json.
"""
import json, subprocess, sys, re
from pathlib import Path

folder = Path(sys.argv[1])
cfg = json.loads((folder / "config.json").read_text())
B = int(cfg["branch_id"]); ROOT = cfg.get("repo_root", "/Users/TruongDinhDucTri/Work/ThreeSides")
after = folder / "after"

def sh(cmd):
    return subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True).stdout

rb = f'''
inst = Therapists::Institute.find_by(institute_code: {json.dumps(cfg["institute_code"])})
ther = Therapists::Employment.where(institute_id: {cfg["rails_institute_id"]}).map(&:therapist).compact.find {{ |t| t.staff_code == {json.dumps(cfg["pro_staff_code"])} }} || Therapists::Employment.where(institute_id: {cfg["rails_institute_id"]}).first.therapist
require 'fileutils'; FileUtils.mkdir_p('/tmp/bfexports')
specs = {{
  export_history:     [::Therapists::Analytics::Report::TicketsPacksExcelGenerator::RESOUCRE_NAME, 'pro_history_after.xlsx'],
  export_performance: [::Therapists::Analytics::Report::TicketsPacksPerformanceReportExcelGenerator::RESOUCRE_NAME, 'pro_performance_after.xlsx'],
  export_annual:      [::Therapists::Analytics::Report::TicketsPacksAnnualReportExcelGenerator::RESOUCRE_NAME, 'pro_annual_after.xlsx'],
}}
filters = {{ branch_ids: [{B}] }}
specs.each do |action, (resource, fname)|
  dl = ::Downloads::Download.create!(therapist_id: ther.id, status: 'in_progress', resource: resource, options: {{ export_file_attributes: nil }})
  begin
    ::Analytics::TicketsPacksReportGenerationJob.perform_now({{ institute: inst, filters: filters, download: dl }})
    dl.reload
    if dl.file.attached?
      File.open(File.join('/tmp/bfexports', fname), 'wb') {{ |f| f.write(dl.file.download) }}
      puts "EXPORT_OK=" + fname + ":" + File.size(File.join('/tmp/bfexports', fname)).to_s
    else
      puts "EXPORT_FAIL=" + fname + ":completion=" + dl.completion_percentage.to_s
    end
  rescue => e
    puts "EXPORT_ERR=" + fname + ":" + e.class.to_s
  end
end
'''
(folder / "_gen_exports.rb").write_text(rb)
sh(f'docker compose cp {json.dumps(str(folder / "_gen_exports.rb"))} threease_backend:/tmp/_gen_exports.rb')
out = sh('docker compose exec -T threease_backend bundle exec rails runner /tmp/_gen_exports.rb')

results = {}
for line in out.splitlines():
    m = re.match(r"^EXPORT_(OK|FAIL|ERR)=([^:]+):(.*)$", line.strip())
    if m:
        status, fname, info = m.groups()
        results[fname] = {"status": status, "info": info}
        if status == "OK":
            sh(f'docker compose cp threease_backend:/tmp/bfexports/{fname} {json.dumps(str(after / fname))}')

(folder / "exports.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
ok = sum(1 for v in results.values() if v["status"] == "OK")
print(f"OK gen_exports.py: {ok}/3 file xlsx → after/")
for k, v in results.items():
    print(f"  {v['status']} {k} ({v['info']})")
