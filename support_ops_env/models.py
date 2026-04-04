from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from support_ops_env.openenv_compat import Action, Observation, State


ActionType = Literal[
    "list_tickets",
    "open_ticket",
    "classify_ticket",
    "assign_ticket",
    "reply_ticket",
    "set_status",
    "submit_task",
    "noop",
]

TicketStatus = Literal["open", "pending_customer", "escalated", "resolved"]
TicketCategory = Literal["account_access", "billing", "bug_report", "security", "shipping"]
TicketPriority = Literal["low", "normal", "high", "urgent"]
TicketTeam = Literal["general_support", "identity_support", "billing_ops", "engineering", "security_response"]


class TicketSnapshot(BaseModel):
    ticket_id: str
    customer_name: str
    subject: str
    customer_tier: Literal["standard", "pro", "enterprise"]
    status: TicketStatus
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    assigned_team: TicketTeam | None = None
    customer_message: str
    latest_reply: str | None = None


class SupportOpsAction(Action):
    action_type: ActionType = Field(description="The support workflow action to take next.")
    ticket_id: str | None = Field(default=None, description="Ticket id for targeted actions.")
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    team: TicketTeam | None = None
    status: TicketStatus | None = None
    message: str | None = Field(default=None, description="Customer-facing reply or final summary.")


class SupportOpsObservation(Observation):
    task_id: str
    task_title: str
    instruction: str
    queue_overview: list[str]
    active_ticket: TicketSnapshot | None = None
    recent_events: list[str]
    progress_score: float = Field(ge=0.0, le=1.0)
    remaining_steps: int
    done: bool = False


class ScoreBreakdown(BaseModel):
    ticket_scores: dict[str, float]
    aggregate_score: float = Field(ge=0.0, le=1.0)
    completed_objectives: list[str]
    missing_objectives: list[str]


class SupportOpsState(State):
    task_id: str
    step_count: int
    max_steps: int
    active_ticket_id: str | None
    tickets: list[TicketSnapshot]
    score_breakdown: ScoreBreakdown
    action_history: list[str]
