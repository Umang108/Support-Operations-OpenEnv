# Support Ops OpenEnv

`support-ops-openenv` is a complete OpenEnv-style environment that simulates a real customer support operations workflow. An agent works through an inbox, classifies tickets, routes them to the correct team, replies to customers, updates status, and finally submits the queue for grading.

The design follows the course structure from `raun/openenv-course` and the standard OpenEnv three-part pattern:

1. Typed `Action`, `Observation`, and `State` models
2. A server-side environment implementing `reset()`, `step()`, and `state()`
3. A typed client plus containerized deployment assets

## Environment Summary

It models a task human support teams perform every day:

- triaging account access tickets
- escalating duplicate billing issues
- handling mixed customer queues with security, bug, and shipping cases

The environment exposes partial progress through reward shaping, while deterministic graders convert final task state into a score from `0.0` to `1.0`.

## Tasks

Three tasks are included, with increasing difficulty:

1. `easy_password_reset`
   A single account-access ticket that should be classified, routed to identity support, replied to, and resolved.
2. `medium_duplicate_charge`
   An enterprise billing issue in a small queue. The agent must correctly prioritize the real billing problem without over-processing the unrelated suggestion ticket.
3. `hard_mixed_queue`
   A full inbox containing a phishing report, a production webhook incident, and a shipment delay. The agent must triage the whole queue correctly.

## Action Space

The environment uses one typed action model, `SupportOpsAction`, with these `action_type` values:

- `list_tickets`
- `open_ticket`
- `classify_ticket`
- `assign_ticket`
- `reply_ticket`
- `set_status`
- `submit_task`
- `noop`

Optional typed fields on the action include:

- `ticket_id`
- `category`
- `priority`
- `team`
- `status`
- `message`

## Observation Space

Each `SupportOpsObservation` includes:

- `task_id` and `task_title`
- the natural-language `instruction`
- `queue_overview`
- the currently opened `active_ticket`
- `recent_events`
- `progress_score`
- `remaining_steps`
- `done`

## Reward Design

Reward is dense rather than purely terminal:

- small positive rewards for meaningful workflow actions
- score-delta reward whenever the ticket state becomes more aligned with the task rubric
- penalties for invalid actions, no-ops, and running out of steps
- a small submit bonus for high-quality final submissions

This gives agents partial progress signals over the whole trajectory.

## Graders

Each task has a deterministic rubric in [`support_ops_env/task_bank.py`](/d:/TCS_Work/Oprn_env/support_ops_env/task_bank.py). Grading checks exact end-state values for:

- category
- priority
- assigned team
- status
- reply keyword coverage

The final score is a weighted average over ticket goals and is always in the range `0.0` to `1.0`.

## Project Layout

- [`support_ops_env/models.py`](/d:/TCS_Work/Oprn_env/support_ops_env/models.py): typed Pydantic models
- [`support_ops_env/server/support_ops_environment.py`](/d:/TCS_Work/Oprn_env/support_ops_env/server/support_ops_environment.py): main environment logic
- [`support_ops_env/graders.py`](/d:/TCS_Work/Oprn_env/support_ops_env/graders.py): deterministic grading
- [`scripts/run_baseline.py`](/d:/TCS_Work/Oprn_env/scripts/run_baseline.py): OpenAI baseline runner
- [`openenv.yaml`](/d:/TCS_Work/Oprn_env/openenv.yaml): environment metadata
- [`Dockerfile`](/d:/TCS_Work/Oprn_env/Dockerfile): container image for local runs and Hugging Face Spaces

## Setup

```bash
uv sync --dev
```

## Local Usage

Run the environment server:

```bash
python -m support_ops_env.server
```

Run the tests:

```bash
pytest
```

If you have OpenEnv installed, validate the package from the project root:

```bash
openenv validate
```

## Baseline Inference

The baseline script prefers Azure OpenAI credentials and reads `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, and `AZURE_OPENAI_API_VERSION`. It falls back to `OPENAI_API_KEY` if Azure settings are not provided.

```bash
$env:AZURE_OPENAI_API_KEY=""
$env:AZURE_OPENAI_ENDPOINT=""
$env:AZURE_OPENAI_DEPLOYMENT=""
$env:AZURE_OPENAI_API_VERSION=""
python scripts/run_baseline.py
```

It evaluates all three tasks and writes a reproducible result file to `baseline_results.json`.

## Docker

Build and run locally:

```bash
docker build -t support-ops-env .
docker run --env-file .env -p 7860:7860 support-ops-env
```

## Hugging Face Spaces

Create a Docker Space and tag it with `openenv`, then push this repository with the included root [`Dockerfile`](/d:/TCS_Work/Oprn_env/Dockerfile).

Recommended Space settings:

- SDK: `Docker`
- Port: `7860`
- Python: `3.11`

Once deployed, the environment can be served through the standard OpenEnv container workflow.
