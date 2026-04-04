# Complete Setup & Deployment Guide

This guide covers all aspects of setting up, testing, deploying, and using the **Support Operations OpenEnv** environment.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Setup](#development-setup)
3. [Running the Environment](#running-the-environment)
4. [Testing](#testing)
5. [Baseline Inference](#baseline-inference)
6. [Docker Setup](#docker-setup)
7. [Hugging Face Deployment](#hugging-face-deployment)
8. [Project Architecture](#project-architecture)
9. [Environment API Reference](#environment-api-reference)

---

## Quick Start

### Prerequisites

- Python 3.11+
- uv
- (Optional) Docker for containerized runs
- (Optional) Azure OpenAI credentials for baseline inference

### Installation

```bash
# Clone or navigate to the project directory
cd support-ops-openenv

# Create the project virtual environment and install locked dependencies
uv sync --dev
```

### Quick Test

```bash
# Run the test suite
pytest

# Expected output:
# tests/test_support_ops_env.py::test_easy_task_can_reach_full_score PASSED
# tests/test_support_ops_env.py::test_invalid_action_is_penalized PASSED
```

### Run the Server

```bash
# Start the FastAPI server on port 7860
python -m support_ops_env.server

# The server will print:
# INFO: Started server process [PID]
# INFO: Uvicorn running on http://0.0.0.0:7860
```

Check health:

```bash
curl http://localhost:7860/health
# Returns: {"status":"ok"}
```

---

## Development Setup

### Step 1: Clone and Setup Environment

```bash
git clone <repository-url>
cd support-ops-openenv
uv sync --dev
``` 

### Step 2: Install Development Dependencies

```bash
uv sync --dev
``` 

This installs through `uv` using `pyproject.toml` and `uv.lock`:

- Core dependencies for the environment runtime
- Dev dependencies including `pytest`

### Step 3: Verify Installation

```bash
# Check imports work
python -c "from support_ops_env import SupportOpsEnv; print('Success')"

# Run tests
pytest -v

# Check code quality (optional)
python -m py_compile support_ops_env/**/*.py
```

---

## Running the Environment

### 1. Direct Python Usage (Local)

```python
from support_ops_env import SupportOpsEnv
from support_ops_env.models import SupportOpsAction

# Create environment
env = SupportOpsEnv()

# Reset to a task
observation = env.reset(task_id="easy_password_reset").observation

# Take actions
action = SupportOpsAction(
    action_type="open_ticket",
    ticket_id="T-100"
)
result = env.step(action)

print(f"Reward: {result.reward}")
print(f"Done: {result.done}")
print(f"Progress: {result.observation.progress_score}")

# Get current state
state = env.state()
print(f"Step count: {state.step_count}")
print(f"Score breakdown: {state.score_breakdown}")
```

### 2. HTTP Server

Start the server:

```bash
python -m support_ops_env.server
```

Make HTTP requests:

**Health Check:**

```bash
curl http://localhost:7860/health
```

**Reset:**

```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_password_reset"}'
```

**Step:**

```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "list_tickets",
    "ticket_id": null
  }'
```

**Get State:**

```bash
curl http://localhost:7860/state
```

### 3. Available Tasks

```python
from support_ops_env.task_bank import list_task_ids

print(list_task_ids())
# Output: ['easy_password_reset', 'hard_mixed_queue', 'medium_duplicate_charge']
```

**Easy Task: `easy_password_reset`**

- 1 ticket to triage
- Max 8 steps
- Objective: Classify password reset issue, assign to identity team, reply to customer, resolve

**Medium Task: `medium_duplicate_charge`**

- 2 tickets to handle
- Max 10 steps
- Objective: Find the billing issue, correctly prioritize it, handle with proper routing

**Hard Task: `hard_mixed_queue`**

- 3 tickets with different priorities
- Max 16 steps
- Objective: Correctly triage security issue, production bug, and shipping complaint

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_support_ops_env.py::test_easy_task_can_reach_full_score

# Run with coverage (optional, requires pytest-cov)
pytest --cov=support_ops_env
```

### Test Files

- **`tests/test_support_ops_env.py`**: Core environment tests
  - `test_easy_task_can_reach_full_score`: Verifies agent can achieve 1.0 score on easy task
  - `test_invalid_action_is_penalized`: Verifies invalid actions are penalized

### Adding Tests

Create tests in `tests/` directory following pytest conventions:

```python
def test_my_feature():
    from support_ops_env import SupportOpsEnv
    from support_ops_env.models import SupportOpsAction

    env = SupportOpsEnv()
    obs = env.reset(task_id="easy_password_reset").observation

    assert obs.task_id == "easy_password_reset"
    assert len(obs.queue_overview) == 1
```

---

## Baseline Inference

### Overview

The baseline script uses OpenAI's API to run an agent through all three tasks and measure performance.

### Prerequisites

1. Azure OpenAI credentials
2. Environment variables set in your shell or `.env`

### Running Baseline

```bash
$env:AZURE_OPENAI_API_KEY=""
$env:AZURE_OPENAI_ENDPOINT=""
$env:AZURE_OPENAI_DEPLOYMENT=""
$env:AZURE_OPENAI_API_VERSION=""

# Run baseline with the configured Azure deployment
python scripts/run_baseline.py

# Or specify a different model
python scripts/run_baseline.py --model gpt-4.1

# Specify output file
python scripts/run_baseline.py --output results.json
```

### Output

The script produces `baseline_results.json`:

```json
{
  "model": "gpt-4.1",
  "average_score": 0.65,
  "results": [
    {
      "task_id": "easy_password_reset",
      "score": 0.75,
      "steps": 6,
      "cumulative_reward": 0.45,
      ...
    },
    {
      "task_id": "medium_duplicate_charge",
      "score": 0.60,
      "steps": 8,
      ...
    },
    {
      "task_id": "hard_mixed_queue",
      "score": 0.60,
      "steps": 12,
      ...
    }
  ]
}
```

### Expected Results

- **Easy task**: 0.8+ (straightforward single issue)
- **Medium task**: 0.6-0.8 (requires filtering unrelated tickets)
- **Hard task**: 0.4-0.7 (complex multi-ticket queue with different priorities)

---

## Docker Setup

### Building the Image

```bash
# Build locally
docker build -t support-ops-env .

# With a specific platform (for cross-compilation)
docker build --platform linux/amd64 -t support-ops-env .
```

### Running Container

```bash
# Run the environment server
docker run --env-file .env -p 7860:7860 support-ops-env

# Verify it's running
curl http://localhost:7860/health
```

### Dockerfile Details

The provided `Dockerfile`:

- Uses `python:3.11-slim` base image (minimal footprint)
- Installs dependencies efficiently with `--no-cache-dir`
- Exposes port 7860 for the FastAPI server
- Sets environment variables for production (no bytecode, unbuffered output)
- Uses the command `python -m support_ops_env.server` as entrypoint

### Multi-stage Builds (Optional)

For smaller images, you can create a multi-stage build:

```dockerfile
FROM python:3.11-slim as builder
WORKDIR /build
COPY . .
RUN uv sync --frozen --no-dev

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY support_ops_env ./support_ops_env
EXPOSE 7860
CMD ["python", "-m", "support_ops_env.server"]
```

---

## Hugging Face Deployment

### Prerequisites

1. Hugging Face account (https://huggingface.co/join)
2. `huggingface-hub` CLI installed: `uv tool install huggingface-hub`
3. Hugging Face API token

### Step 1: Create a Space

1. Go to https://huggingface.co/new-space
2. Choose a name: `support-ops-openenv`
3. Select **Docker** as the SDK
4. Set **Port** to `7860`
5. Create the space

### Step 2: Push Code to Space

```bash
# Add the HF remote
git remote add hf https://huggingface.co/spaces/{YOUR_USERNAME}/support-ops-openenv

# Push code
git push hf main

# Or if you want to push a specific branch:
git push hf main:main
```

### Step 3: Configure Space Settings

In the Space settings:

- **SDK**: Docker
- **Port**: 7860
- **Tags**: `openenv`, `customer-support`, `rl-environment`
- **Python Version**: 3.11

### Step 4: Verify Deployment

Once the Space finishes building (2-10 minutes), you'll see:

- ✅ Deployment status
- Direct URL to access the environment
- Real-time logs

### Accessing Deployed Environment

```bash
# Via HTTP
curl https://{YOUR_USERNAME}-support-ops-openenv.hf.space/health

# Via Python (if openenv-core is installed)
from openenv import RemoteClient
client = RemoteClient(
    url="https://{YOUR_USERNAME}-support-ops-openenv.hf.space"
)
obs = client.reset(task_id="easy_password_reset")
```

### Troubleshooting Deployment

- **Build fails**: Check logs in Space settings → Build logs
- **Port issues**: Ensure Dockerfile and `__main__.py` use port 7860
- **ImportError**: Verify all files are committed and `pyproject.toml` is correct
- **OOM**: Add memory limit in Space settings or optimize dependencies

---

## Project Architecture

### Directory Structure

```
support-ops-openenv/
├── support_ops_env/           # Main package
│   ├── __init__.py
│   ├── models.py              # Pydantic models (Action, Observation, State)
│   ├── client.py              # Typed client wrapper
│   ├── graders.py             # Task grading logic (0.0-1.0 scores)
│   ├── task_bank.py           # Task definitions and data
│   ├── openenv_compat.py      # Compatibility with openenv-core
│   └── server/
│       ├── __init__.py
│       ├── app.py             # FastAPI app setup
│       ├── __main__.py        # Server entrypoint
│       └── support_ops_environment.py  # Core simulator logic
├── scripts/
│   └── run_baseline.py        # OpenAI baseline inference
├── tests/
│   ├── __init__.py
│   └── test_support_ops_env.py
├── pyproject.toml             # Package metadata
├── openenv.yaml               # OpenEnv spec
├── Dockerfile                 # Container image definition
├── README.md                  # User-facing documentation
├── SETUP.md                   # This file
├── requirements.txt           # Alternative dependency specification
└── .gitignore

```

### Core Modules

**`models.py`**

- `SupportOpsAction`: What the agent can do (typed)
- `SupportOpsObservation`: What the agent sees (typed)
- `SupportOpsState`: Full environment state
- `TicketSnapshot`: Individual ticket representation

**`server/support_ops_environment.py`**

- `SupportOpsEnvironment` class
  - `reset(task_id)`: Initialize episode
  - `step(action)`: Execute action, return reward + observation
  - `state()`: Get full state snapshot

**`task_bank.py`**

- `TASKS`: Dictionary of 3 predefined tasks
- `TaskDefinition`: Task schema with goals, max steps, instructions
- `TicketGoal`: Per-ticket grading criteria
- `ReplyRequirement`: Keyword matching for replies

**`graders.py`**

- `grade_task()`: Main grading function
- `_score_ticket()`: Per-ticket scoring (0.0-1.0)
- `_score_reply()`: Keyword matching for customer replies

---

## Environment API Reference

### Reset

```python
observation = env.reset(task_id: str = "easy_password_reset")
```

**Parameters:**

- `task_id` (string): One of `["easy_password_reset", "medium_duplicate_charge", "hard_mixed_queue"]`

**Returns:** `StepResult` with:

- `observation: SupportOpsObservation`
- `reward: 0.0` (initial)
- `done: False`
- `info: {"source": "local"}`

---

### Step

```python
result = env.step(action: SupportOpsAction)
```

**Parameters:**

- `action`: Action with type and optional fields

**Action Types:**

| Action            | Fields                              | Effect                     |
| ----------------- | ----------------------------------- | -------------------------- |
| `list_tickets`    | -                                   | Returns queue overview     |
| `open_ticket`     | `ticket_id`                         | Sets active ticket         |
| `classify_ticket` | `ticket_id`, `category`, `priority` | Sets ticket classification |
| `assign_ticket`   | `ticket_id`, `team`                 | Assigns to support team    |
| `reply_ticket`    | `ticket_id`, `message`              | Sends customer reply       |
| `set_status`      | `ticket_id`, `status`               | Updates ticket status      |
| `submit_task`     | `message` (optional)                | Submits task for grading   |
| `noop`            | -                                   | No-op (penalized)          |

**Returns:** `StepResult` with:

- `observation: SupportOpsObservation` (updated)
- `reward: float` (between -0.2 and +0.1)
- `done: bool` (True if task submitted or max steps reached)
- `info: dict` (metadata including score breakdown)

---

### State

```python
state = env.state()
```

**Returns:** `SupportOpsState` with:

- `task_id: str`
- `step_count: int`
- `max_steps: int`
- `active_ticket_id: str | None`
- `tickets: list[TicketSnapshot]`
- `score_breakdown: ScoreBreakdown`
- `action_history: list[str]`

---

### Observation Fields

```python
observation.task_id              # Current task ID
observation.task_title           # Human-readable task name
observation.instruction          # Task description
observation.queue_overview       # List of ticket summaries
observation.active_ticket        # Currently open ticket (or None)
observation.recent_events        # Human-readable event log
observation.progress_score       # Current task score (0.0-1.0)
observation.remaining_steps      # Steps left before episode ends
observation.done                 # Whether episode is finished
```

---

### Reward Structure

Rewards are shaped to provide learning signal throughout the episode:

| Event                                   | Reward              |
| --------------------------------------- | ------------------- |
| Base (per step)                         | -0.01               |
| List tickets                            | 0.0                 |
| Classify ticket                         | +0.02               |
| Assign ticket                           | +0.02               |
| Reply to customer                       | +0.03               |
| Set status                              | +0.02               |
| Invalid action                          | -0.10               |
| No-op (noop)                            | -0.03               |
| Score improvement                       | +delta (up to +1.0) |
| Submit high-quality task (score >= 0.8) | +0.10               |
| Submit low-quality task                 | -0.10               |
| Exceed max steps                        | -0.15               |

---

## Troubleshooting

### Common Issues

**Issue: "ModuleNotFoundError: No module named 'openenv'"**

- **Solution**: `openenv-core` is optional. The package works standalone via the fallback in `openenv_compat.py`.

**Issue: "ImportError: cannot import name 'SupportOpsEnv'"**

- **Solution**: Ensure installation with `uv sync --dev` from the project root.

**Issue: Tests fail with "NameError"**

- **Solution**: Activate your virtual environment: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux)

**Issue: Docker build fails with "no such file"**

- **Solution**: Run docker build from the project root where `Dockerfile` is located.

**Issue: Server won't start on port 7860**

- **Solution**: Port may be in use. Change in `support_ops_env/server/__main__.py`:
  ```python
  uvicorn.run(..., port=8000)  # Use different port
  ```

**Issue: Baseline inference is slow**

- **Solution**: Use a faster Azure deployment, or pass `--model <deployment_name>` to target a different deployment.

---

## Next Steps

1. **Run tests**: `pytest -v`
2. **Try baseline**: `python scripts/run_baseline.py` (requires Azure OpenAI credentials, or `OPENAI_API_KEY` as fallback)
3. **Deploy locally**: `python -m support_ops_env.server`
4. **Deploy to HF**: Push to Hugging Face Space
5. **Develop agents**: Use the environment in your RL/LLM training pipeline

---

## Citation

If you use this environment, please cite:

```bibtex
@software{support_ops_openenv_2024,
  title={Support Operations OpenEnv Environment},
  author={Your Name},
  year={2024},
  url={https://github.com/yourname/support-ops-openenv}
}
```

---

## License

MIT License - See LICENSE file for details.








