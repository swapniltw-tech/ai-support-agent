from policypal.config import Settings

def test_settings_reads_values(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_MODEL", "some-model")
    s = Settings(_env_file=None)
    assert s.anthropic_model == "some-model"
    assert s.anthropic_api_key.get_secret_value() == "sk-test"