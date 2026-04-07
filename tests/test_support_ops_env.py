from fastapi.testclient import TestClient

from scripts.run_baseline import build_client_and_model
from support_ops_env.models import SupportOpsAction
from support_ops_env.server.app import app
from support_ops_env.server.support_ops_environment import SupportOpsEnvironment


def test_easy_task_can_reach_full_score() -> None:
    env = SupportOpsEnvironment()
    env.reset(task_id="easy_password_reset")
    env.step(SupportOpsAction(action_type="open_ticket", ticket_id="T-100"))
    env.step(
        SupportOpsAction(
            action_type="classify_ticket",
            ticket_id="T-100",
            category="account_access",
            priority="normal",
        )
    )
    env.step(SupportOpsAction(action_type="assign_ticket", ticket_id="T-100", team="identity_support"))
    env.step(
        SupportOpsAction(
            action_type="reply_ticket",
            ticket_id="T-100",
            message="I have sent a fresh password reset link so you can log in to your account again.",
        )
    )
    env.step(SupportOpsAction(action_type="set_status", ticket_id="T-100", status="resolved"))
    result = env.step(SupportOpsAction(action_type="submit_task", message="done"))
    assert result.done is True
    score = env.state().score_breakdown.aggregate_score
    assert 0.0 < score < 1.0
    assert score >= 0.99


def test_invalid_action_is_penalized() -> None:
    env = SupportOpsEnvironment()
    env.reset(task_id="easy_password_reset")
    result = env.step(SupportOpsAction(action_type="assign_ticket", ticket_id="T-100"))
    assert result.reward < 0
    assert "error" in result.info


def test_openapi_schema_is_available() -> None:
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["openapi"].startswith("3.")


def test_build_client_uses_groq(monkeypatch) -> None:
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("MODEL", "llama-3.3-70b-versatile")

    client, model = build_client_and_model(None)

    assert client.__class__.__name__ == "OpenAI"
    assert client.api_key == "test-key"
    assert str(client.base_url) == "https://api.groq.com/openai/v1/"
    assert model == "llama-3.3-70b-versatile"


def test_build_client_uses_hf_token(monkeypatch) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf-test-key")
    monkeypatch.setenv("API_BASE_URL", "https://router.huggingface.co/v1")
    monkeypatch.setenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    client, model = build_client_and_model(None)

    assert client.__class__.__name__ == "OpenAI"
    assert client.api_key == "hf-test-key"
    assert str(client.base_url) == "https://router.huggingface.co/v1/"
    assert model == "Qwen/Qwen2.5-72B-Instruct"
