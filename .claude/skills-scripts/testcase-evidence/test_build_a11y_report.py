# Chạy: python3 test_build_a11y_report.py  → in "✅ ... PASS" nếu ổn.
import json, os, subprocess, sys, tempfile
from openpyxl import load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    results = {
        "meta": {"case": "T", "date": "2026-07-16", "tester": "QA-Server-a11y"},
        "screens": [{
            "name": "Đặt lịch", "app": "reservation", "url": "/booking", "result": "FAIL",
            "violations": [{
                "rule": "button-name", "impact": "serious", "wcag": "4.1.2",
                "help": "Buttons must have discernible text",
                "nodes": [{"target": "button.v-btn", "html": "<button></button>"}]
            }]
        }]
    }
    with tempfile.TemporaryDirectory() as d:
        rp = os.path.join(d, "a11y.results.json")
        with open(rp, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False)
        out = os.path.join(d, "T.a11y.xlsx")
        subprocess.run([sys.executable, os.path.join(HERE, "build_a11y_report.py"), rp, out], check=True)
        ws = load_workbook(out)["Accessibility"]
        assert ws.cell(1, 4).value == "Rule", f"header sai: {ws.cell(1,4).value}"
        assert ws.cell(2, 4).value == "button-name", f"rule sai: {ws.cell(2,4).value}"
        assert ws.cell(2, 5).value == "serious", f"impact sai: {ws.cell(2,5).value}"
    print("✅ test_build_a11y_report PASS")

if __name__ == "__main__":
    main()
