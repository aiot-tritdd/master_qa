import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

QA_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(QA_ROOT / ".env")

def _p(env, default): return Path(os.getenv(env, default))

@dataclass(frozen=True)
class Settings:
    qa_root: Path = QA_ROOT
    threesides_root: Path = _p("THREESIDES_ROOT", "/Users/tritdd/Work/ThreeSides")
    compose_file: Path = _p("COMPOSE_FILE", "/Users/tritdd/Work/ThreeSides/docker-compose.yml")
    knowledge_dir: Path = QA_ROOT / "knowledge"
    generated_dir: Path = QA_ROOT / "tests_generated"
    cache_dir: Path = QA_ROOT / ".qa_cache"
    backend_service: str = os.getenv("BACKEND_SERVICE", "threease_backend")
    ticket_service: str = os.getenv("TICKET_SERVICE", "threease_ticket")
    ticket_db_service: str = os.getenv("TICKET_DB_SERVICE", "postgres14_ticket")
    ticket_admin_key: str = os.getenv("TICKET_ADMIN_KEY", "local-dev-key")
    ticket_admin_secret: str = os.getenv("TICKET_ADMIN_SECRET", "local-dev-secret-32-chars-minimum!")
    ticket_base_url: str = os.getenv("TICKET_BASE_URL", "http://127.0.0.1:8000")
    sync_start_id: int = int(os.getenv("SYNC_START_ID", "200000"))

settings = Settings()
