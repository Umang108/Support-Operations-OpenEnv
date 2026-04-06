from __future__ import annotations

import json
import os
from typing import Optional

from openai import OpenAI

from support_ops_env.models import SupportOpsAction
from support_ops_env.server.support_ops_environment import SupportOpsEnvironment
from support_ops_env.task_bank import list_task_ids


# Mandatory environment configuration for evaluator compatibility.
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

BENCHMARK = "support_ops_env"
MAX_AGENT_STEPS = 16

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


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{reward:.2f}" for reward in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def choose_action(
    client: OpenAI,
    task_id: str,
    observation: dict,
    history: list[dict],
) -> SupportOpsAction:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
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
    except Exception:
        # Keep episodes moving when model calls are unavailable.
        return SupportOpsAction(action_type="list_tickets")


def run_task(client: OpenAI, task_id: str) -> None:
    env = SupportOpsEnvironment()
    rewards: list[float] = []
    history: list[dict] = []
    steps_taken = 0
    success = False
    score = 0.0

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        observation = env.reset(task_id=task_id)
        done = False

        for step in range(1, MAX_AGENT_STEPS + 1):
            if done:
                break

            action = choose_action(client, task_id, observation.model_dump(), history)
            result = env.step(action)

            error = None
            if isinstance(result.info, dict):
                error = result.info.get("error")

            reward = float(result.reward or 0.0)
            rewards.append(reward)
            steps_taken = step
            done = bool(result.done)

            action_str = action.model_dump_json(exclude_none=True)
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            history.append(
                {
                    "action": action.model_dump(exclude_none=True),
                    "reward": reward,
                    "done": done,
                    "error": error,
                }
            )
            observation = result.observation

            if done:
                break

        if not done:
            final_result = env.step(
                SupportOpsAction(action_type="submit_task", message="Submitting unfinished task for grading.")
            )
            reward = float(final_result.reward or 0.0)
            rewards.append(reward)
            steps_taken += 1
            done = bool(final_result.done)

            error = None
            if isinstance(final_result.info, dict):
                error = final_result.info.get("error")

            log_step(
                step=steps_taken,
                action='{"action_type":"submit_task","message":"Submitting unfinished task for grading."}',
                reward=reward,
                done=done,
                error=error,
            )

        state = env.state()
        score = float(state.score_breakdown.aggregate_score)
        score = min(max(score, 0.0), 1.0)
        success = score >= 0.1
    except Exception:
        success = False
        state = env.state()
        score = float(state.score_breakdown.aggregate_score)
        score = min(max(score, 0.0), 1.0)
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


def main() -> None:
    if not HF_TOKEN:
        raise SystemExit("Missing HF_TOKEN environment variable.")

    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    # Keep reference for docker-image based variants expected by some validators.
    _ = LOCAL_IMAGE_NAME

    for task_id in list_task_ids():
        run_task(client, task_id)


if __name__ == "__main__":
    main()