# threease_qa — QA-Server (Phase 1 MVP)

Con QA-senior nhân tạo **hiểu nghiệp vụ** của hệ ThreeSides: tự sinh tài liệu sống
từ code → người duyệt qua UI (nguồn ý định) → sinh + chạy pytest từ **ý định đã duyệt**
trên stack docker thật. Lát dọc đầu tiên: luồng **customer-sync (backend ↔ ticket)**.

Tài liệu tổng (why/what/how, roadmap): [`docs/QA-SERVER.md`](docs/QA-SERVER.md).

## Kiến trúc — 2 tầng

```
web/ (Next.js 14, port 3001)  ──HTTP──▶  api/ (FastAPI, port 8899)  ──▶  qa/ (pipeline Python)
   Ghibli UI, mặt tiền                    JSON API bọc pipeline           llm · gitnexus · knowledge
                                                                          extractor · testgen · runner
```
Pipeline **bắt buộc** Python (shell ra `claude` / `pytest` / `docker compose` / `gitnexus`).
Next.js chỉ là mặt tiền gọi API. Knowledge = markdown + YAML front-matter trong git, **no DB**.

## Setup

```bash
cp .env.example .env
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
```

## Prereqs

- ThreeSides docker stack chạy: `cd ../ThreeSides && docker compose up -d`
- `claude` CLI + `gitnexus` trên PATH.

## Chạy (2 terminal)

```bash
# Terminal 1 — API (FastAPI)
source venv/bin/activate
uvicorn api.app:app --reload --port 8899

# Terminal 2 — UI (Next.js)
cd web && npm install && npm run dev     # http://localhost:3001
```

## Lát dọc (bấm trong UI)

1. **① Sinh doc nháp** → sinh `knowledge/customer-sync.md` (status `draft`).
2. **Xem / Duyệt doc** → đọc, rồi **✅ Duyệt (Approve)** → flip `approved` + git commit (chốt ý định).
3. **③ Sinh test** → sinh `tests_generated/test_customer_sync.py` từ doc **đã duyệt** (cấm đọc code).
4. **④ Chạy test** → tạo customer bằng `rails runner` → chờ/flush outbox → assert đã sync sang ticket → ✅ PASS.

## Test

```bash
source venv/bin/activate
python -m pytest -q        # unit tests (pure logic: llm parser, knowledge, testgen guard, runner, api)
```

> Unit test **không** đụng stack docker (dùng fakes). Test đẻ ra (`tests_generated/`) mới
> chạy thật trên stack — chạy qua nút **④ Chạy test** hoặc `runner.run_generated()`.

Demo phá-code / đổi-ý: xem [`docs/DEMO.md`](docs/DEMO.md).
