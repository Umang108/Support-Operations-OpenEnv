from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from support_ops_env.models import SupportOpsAction
from support_ops_env.server.support_ops_environment import SupportOpsEnvironment
from support_ops_env.task_bank import list_task_ids


SYSTEM_PROMPT = """You are operating a customer-support triage environment.
Return exactly one JSON object matching this schema:
{
  \"action_type\": \"list_tickets|open_ticket|classify_ticket|assign_ticket|reply_ticket|set_status|submit_task|noop\",
  \"ticket_id\": \"optional string\",
  \"category\": \"optional\",
  \"priority\": \"optional\",
  \"team\": \"optional\",
  \"status\": \"optional\",
  \"message\": \"optional\"
}
Choose the single best next action. Do not include markdown fences."""


_CATEGORY_ALIASES = {
    "account access": "account_access",
    "account_access": "account_access",
    "account-access": "account_access",
    "billing": "billing",
    "bug report": "bug_report",
    "bug_report": "bug_report",
    "bug-report": "bug_report",
    "security": "security",
    "shipping": "shipping",
}

_PRIORITY_ALIASES = {
    "low": "low",
    "normal": "normal",
    "medium": "normal",
    "med": "normal",
    "high": "high",
    "urgent": "urgent",
    "critical": "urgent",
    "sev1": "urgent",
}


def _normalize_payload(payload: dict) -> dict:
    normalized = dict(payload)

    category = normalized.get("category")
    if isinstance(category, str):
        key = category.strip().lower().replace("_", " ").replace("-", " ")
        normalized["category"] = _CATEGORY_ALIASES.get(key, category.strip().lower())

    priority = normalized.get("priority")
    if isinstance(priority, str):
        key = priority.strip().lower().replace("_", " ").replace("-", " ")
        normalized["priority"] = _PRIORITY_ALIASES.get(key, priority.strip().lower())

    return normalized


def choose_action(
    client: OpenAI,
    model: str,
    task_id: str,
    observation: dict,
    history: list[dict],
) -> SupportOpsAction:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task_id": task_id,
                        "observation": observation,
                        "recent_action_history": history[-6:],
                    },
                    indent=2,
                ),
            },
        ],
    )
    content = response.choices[0].message.content or "{}"
    payload = json.loads(content)
    normalized_payload = _normalize_payload(payload)

    try:
        return SupportOpsAction.model_validate(normalized_payload)
    except ValidationError:
        # Keep baseline running even when model emits invalid enum variants.
        return SupportOpsAction(action_type="list_tickets")


def run_task(client: OpenAI, model: str, task_id: str, max_agent_steps: int = 12) -> dict:
    env = SupportOpsEnvironment()
    observation = env.reset(task_id=task_id)
    history: list[dict] = []
    cumulative_reward = 0.0
    done = False

    for _ in range(max_agent_steps):
        action = choose_action(client, model, task_id, observation.model_dump(), history)
        result = env.step(action)
        history.append({"action": action.model_dump(), "reward": result.reward, "done": result.done})
        cumulative_reward += result.reward
        observation = result.observation
        done = result.done
        if done:
            break

    if not done:
        final_result = env.step(SupportOpsAction(action_type="submit_task", message="Submitting unfinished task for grading."))
        cumulative_reward += final_result.reward
        observation = final_result.observation

    state = env.state()
    return {
        "task_id": task_id,
        "score": state.score_breakdown.aggregate_score,
        "ticket_scores": state.score_breakdown.ticket_scores,
        "cumulative_reward": round(cumulative_reward, 4),
        "steps": state.step_count,
        "history": history,
        "final_observation": observation.model_dump(),
    }


def build_client_and_model(requested_model: str | None) -> tuple[OpenAI, str]:
    # Preferred generic OpenAI-compatible configuration.
    hf_token = os.getenv("HF_TOKEN")
    api_base_url = os.getenv("API_BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    if hf_token:
        client = OpenAI(api_key=hf_token, base_url=api_base_url or "https://router.huggingface.co/v1")
        return client, requested_model or model_name or "Qwen/Qwen2.5-72B-Instruct"

    # Backward-compatible Groq configuration.
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("MODEL") or os.getenv("GROQ_MODEL")

    if groq_api_key:
        client = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
        return client, requested_model or groq_model or "llama-3.3-70b-versatile"

    raise SystemExit(
        "Missing model credentials. Set HF_TOKEN (and optionally API_BASE_URL, MODEL_NAME) "
        "or set GROQ_API_KEY (and optionally MODEL/GROQ_MODEL)."
    )


def main() -> None:
    # Load local .env automatically for easier local runs.
    if load_dotenv is not None:
        load_dotenv()

    parser = argparse.ArgumentParser(description="Run a baseline against all support ops tasks.")
    parser.add_argument("--model", default=None)
    parser.add_argument("--output", default="baseline_results.json")
    args = parser.parse_args()

    client, model = build_client_and_model(args.model)
    results = [run_task(client, model, task_id) for task_id in list_task_ids()]
    summary = {
        "model": model,
        "average_score": round(sum(item["score"] for item in results) / len(results), 4),
        "results": results,
    }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
