---
title: support-ops-openenv
emoji: "🧰"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Support Ops OpenEnv

A small support-ticket environment for testing agent workflows.

## What It Does

- Loads one of three predefined support queue tasks
- Lets an agent inspect tickets, classify them, assign them, reply, and update status
- Grades the final state with a deterministic scorer

## Main Files

- `support_ops_env/task_bank.py`: predefined ticket scenarios
- `support_ops_env/server/support_ops_environment.py`: environment logic and in-memory ticket state
- `support_ops_env/models.py`: action, observation, state, and ticket models
- `support_ops_env/graders.py`: scoring logic
- `inference.py`: submission inference runner (root-level)
- `scripts/run_baseline.py`: optional local baseline runner

## Run Locally

```bash
uv sync --dev
python -m support_ops_env.server
```

Server runs on `http://127.0.0.1:7860`.
go to `http://127.0.0.1:7860/docs` endpoints

## Submission Inference (Mandatory)

The submission script is `inference.py` in the project root.

Required environment variables:

- `API_BASE_URL` (LLM endpoint, default provided by script)
- `MODEL_NAME` (LLM model id, default provided by script)
- `HF_TOKEN` (required API token)
- `LOCAL_IMAGE_NAME` (optional; for docker-image based environments)

Run:

```bash
python inference.py
```

`inference.py`:

- uses `OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)` for all model calls
- iterates all tasks from `support_ops_env.task_bank.list_task_ids()`
- prints only structured stdout lines in this format:
  - `[START] task=... env=... model=...`
  - `[STEP] step=... action=... reward=0.00 done=true|false error=...|null`
  - `[END] success=true|false steps=... score=... rewards=r1,r2,...`

Each task score is normalized to `(0.0, 1.0)` (strictly between 0 and 1).

## API Endpoints

- `GET /health`
- `POST /reset`
- `POST /step`
- `GET /state`

Example:

```bash
curl http://127.0.0.1:7860/health
```

## Validation

Run repository checks:

```bash
python verify_setup.py
```

Run tests:

```bash
python -m pytest -q
```

If your shell cannot import from the workspace root on Windows PowerShell:

```powershell
$env:PYTHONPATH='.'
python -m pytest -q
```

## Docker

Preferred (compose):

```bash
docker compose up -d --build
```

Check service:

```bash
curl http://127.0.0.1:7860/health
curl -X POST http://127.0.0.1:7860/reset -H "Content-Type: application/json" -d '{"task_id":"easy_password_reset"}'
```

View logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```
