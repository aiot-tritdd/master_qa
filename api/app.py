from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from qa.config import settings
from qa import extractor, testgen, runner, knowledge

app = FastAPI(title="QA-Server API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)
DOC = settings.knowledge_dir / "customer-sync.md"
_last_run: dict | None = None


@app.get("/api/status")
def status():
    meta = knowledge.load(DOC).meta if DOC.exists() else None
    doc = {"status": meta.get("status"), "spans_repos": meta.get("spans_repos")} if meta else None
    return {
        "doc": doc,
        "tests_exist": (settings.generated_dir / "test_customer_sync.py").exists(),
        "last_run": _last_run,
    }


@app.post("/api/extract")
def do_extract():
    extractor.extract()
    return {"ok": True}


@app.get("/api/doc")
def get_doc():
    if not DOC.exists():
        raise HTTPException(404, "doc not extracted yet")
    d = knowledge.load(DOC)
    return {"meta": d.meta, "body": d.body}


@app.post("/api/approve")
def do_approve():
    if not DOC.exists():
        raise HTTPException(404, "doc not extracted yet")
    knowledge.approve(DOC)
    return {"ok": True}


@app.post("/api/generate")
def do_generate():
    try:
        testgen.generate(DOC)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/run")
def do_run():
    global _last_run
    _last_run = runner.run_generated()
    return _last_run
