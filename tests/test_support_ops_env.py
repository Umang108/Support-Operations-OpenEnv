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
    assert env.state().score_breakdown.aggregate_score == 1.0


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


def test_build_client_prefers_azure(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example-resource.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client, model = build_client_and_model(None)

    assert client.__class__.__name__ == "AzureOpenAI"
    assert model == "gpt-4.1"
