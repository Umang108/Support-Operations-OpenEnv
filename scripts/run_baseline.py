from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from openai import AzureOpenAI, OpenAI

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


def choose_action(
    client: OpenAI | AzureOpenAI,
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
    return SupportOpsAction.model_validate(payload)


def run_task(client: OpenAI | AzureOpenAI, model: str, task_id: str, max_agent_steps: int = 12) -> dict:
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


def build_client_and_model(requested_model: str | None) -> tuple[OpenAI | AzureOpenAI, str]:
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    if azure_endpoint and azure_api_key and azure_deployment and azure_api_version:
        client = AzureOpenAI(
            api_key=azure_api_key,
            azure_endpoint=azure_endpoint,
            api_version=azure_api_version,
        )
        return client, requested_model or azure_deployment

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        return OpenAI(api_key=openai_api_key), requested_model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    raise SystemExit(
        "Missing model credentials. Set either AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, "
        "AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION or OPENAI_API_KEY."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an OpenAI baseline against all support ops tasks.")
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
