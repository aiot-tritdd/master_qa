from qa.config import settings

def test_settings_load_defaults():
    assert settings.backend_service == "threease_backend"
    assert settings.ticket_service == "threease_ticket"
    assert settings.sync_start_id == 200000
    assert settings.knowledge_dir.name == "knowledge"
    assert settings.ticket_admin_key  # non-empty
