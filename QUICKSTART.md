# Quick Start Cheat Sheet

## 1-Minute Setup

```bash
# Clone/enter directory
cd support-ops-openenv

# Install and create the project virtualenv from uv.lock
uv sync --dev

# Verify
uv run python verify_setup.py
```

## Run Tests

```bash
pytest
```

Expected: **4 passed**

## Run Environment

```bash
# Start server
python -m support_ops_env.server

# In another terminal, test it
curl http://localhost:7860/health
```

## Quick Python Usage

```python
from support_ops_env import SupportOpsEnv, SupportOpsAction

env = SupportOpsEnv()
obs = env.reset(task_id="easy_password_reset").observation

# Take actions
result = env.step(SupportOpsAction(action_type="list_tickets"))

# Check progress
print(f"Score: {result.observation.progress_score}")
print(f"Done: {result.done}")

# Get full state
state = env.state()
print(f"Final score: {state.score_breakdown.aggregate_score}")
```

## Available Tasks

```
easy_password_reset       (1 ticket, 8 steps)  - Single issue
medium_duplicate_charge   (2 tickets, 10 steps) - Filter unrelated
hard_mixed_queue         (3 tickets, 16 steps)  - Complex triage
```

## Action Cheat Sheet

```python
SupportOpsAction(action_type="list_tickets")

SupportOpsAction(
    action_type="open_ticket",
    ticket_id="T-100"
)

SupportOpsAction(
    action_type="classify_ticket",
    ticket_id="T-100",
    category="account_access",  # or: billing, bug_report, security, shipping
    priority="normal"           # or: low, high, urgent
)

SupportOpsAction(
    action_type="assign_ticket",
    ticket_id="T-100",
    team="identity_support"     # or: general_support, billing_ops, engineering, security_response
)

SupportOpsAction(
    action_type="reply_ticket",
    ticket_id="T-100",
    message="Customer reply text..."
)

SupportOpsAction(
    action_type="set_status",
    ticket_id="T-100",
    status="resolved"           # or: open, pending_customer, escalated
)

SupportOpsAction(action_type="submit_task")

SupportOpsAction(action_type="noop")  # Penalized!
```

## Docker

```bash
# Build
docker build -t support-ops-env .

# Run
docker run --env-file .env -p 7860:7860 support-ops-env

# Test
curl http://localhost:7860/health
```

## Baseline Inference

```bash
# Set Azure OpenAI credentials
$env:AZURE_OPENAI_API_KEY=""
$env:AZURE_OPENAI_ENDPOINT=""
$env:AZURE_OPENAI_DEPLOYMENT=""
$env:AZURE_OPENAI_API_VERSION=""

# Run
python scripts/run_baseline.py

# Check results
cat baseline_results.json
```

## Deploy to Hugging Face Spaces

1. Create Space: https://huggingface.co/new-space (select Docker)
2. Push code:
   ```bash
   git remote add hf https://huggingface.co/spaces/{USER}/support-ops-openenv
   git push hf main
   ```
3. Wait ~5 minutes for build
4. Access at: `https://{user}-support-ops-openenv.hf.space`

## Observation Structure

```python
obs.task_id              # "easy_password_reset"
obs.task_title           # "Password reset triage"
obs.instruction          # Full task description
obs.queue_overview       # ["T-100 | Subject | tier=standard | status=open"]
obs.active_ticket        # TicketSnapshot or None
obs.recent_events        # ["Opened T-100: Reset link expired..."]
obs.progress_score       # 0.0 to 1.0
obs.remaining_steps      # Steps left
obs.done                 # True when episode ends
```

## State Structure

```python
state.task_id                           # Current task
state.step_count                        # Steps taken
state.max_steps                         # Step limit
state.tickets                           # All tickets (list[TicketSnapshot])
state.score_breakdown.aggregate_score   # Final score (0.0-1.0)
state.score_breakdown.completed_objectives  # List of achieved goals
state.score_breakdown.missing_objectives    # List of unmet goals
```

## Ticket Fields

```python
ticket.ticket_id          # "T-100"
ticket.customer_name      # "Nina Patel"
ticket.subject            # "Reset link expired..."
ticket.customer_tier      # "standard" | "pro" | "enterprise"
ticket.status             # open, pending_customer, escalated, resolved
ticket.category           # account_access, billing, bug_report, security, shipping
ticket.priority           # low, normal, high, urgent
ticket.assigned_team      # identity_support, general_support, billing_ops, engineering, security_response
ticket.customer_message   # Full message text
ticket.latest_reply       # Agent's reply or None
```

## Reward Breakdown

- Base per step: -0.01
- List tickets: 0.0
- Classify: +0.02
- Assign: +0.02
- Reply: +0.03
- Set status: +0.02
- Score improvement: +delta
- Invalid action: -0.10
- No-op: -0.03
- Good submit (score >= 0.8): +0.10
- Bad submit: -0.10
- Timeout: -0.15

## Troubleshooting

| Problem                   | Solution                                    |
| ------------------------- | ------------------------------------------- |
| Import error              | `uv sync --dev` from project root           |
| Tests fail                | Activate venv: `.venv\Scripts\activate`     |
| Server port busy          | Change port in `server/__main__.py`         |
| Unicode errors on Windows | Use Python 3.11+                            |
| Docker build fails        | Run from project root where `Dockerfile` is |
| Slow baseline             | Use a faster Azure deployment or pass `--model <deployment_name>` |

## Links

- Full Documentation: [SETUP.md](SETUP.md)
- Implementation Details: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- Source Code: [README.md](README.md)
- Verify Setup: `python verify_setup.py`

## One-Liner Tests

```bash
# All tests pass?
pytest && python verify_setup.py

# Server works?
python -m support_ops_env.server & sleep 2 && curl http://localhost:7860/health

# Docker works?
docker build -t test . && docker run --env-file .env -p 7860:7860 test

# Baseline works? (need Azure OpenAI credentials)
python scripts/run_baseline.py
```






