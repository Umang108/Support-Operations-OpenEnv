from __future__ import annotations

from copy import deepcopy
from typing import Literal

from pydantic import BaseModel

from support_ops_env.models import TicketSnapshot


class ReplyRequirement(BaseModel):
    groups: list[list[str]]
    description: str


class TicketGoal(BaseModel):
    ticket_id: str
    expected_category: str | None = None
    expected_priority: str | None = None
    expected_team: str | None = None
    expected_status: str | None = None
    reply_requirement: ReplyRequirement | None = None
    weight: float = 1.0
    required: bool = True


class TaskDefinition(BaseModel):
    task_id: str
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    instruction: str
    max_steps: int
    tickets: list[TicketSnapshot]
    goals: list[TicketGoal]


TASKS: dict[str, TaskDefinition] = {
    "easy_password_reset": TaskDefinition(
        task_id="easy_password_reset",
        title="Password reset triage",
        difficulty="easy",
        instruction=(
            "A single customer cannot access their account. Triage the ticket, route it to the right team, "
            "send an appropriate customer reply, and update the ticket to its final status."
        ),
        max_steps=8,
        tickets=[
            TicketSnapshot(
                ticket_id="T-100",
                customer_name="Nina Patel",
                subject="Reset link expired before I could use it",
                customer_tier="standard",
                status="open",
                customer_message=(
                    "I requested a password reset, but the link expired before I could log in. "
                    "Can you help me get back into my account?"
                ),
            )
        ],
        goals=[
            TicketGoal(
                ticket_id="T-100",
                expected_category="account_access",
                expected_priority="normal",
                expected_team="identity_support",
                expected_status="resolved",
                reply_requirement=ReplyRequirement(
                    description="Reply should mention a new password reset link and account access.",
                    groups=[["password reset", "reset link"], ["account", "log in"]],
                ),
                weight=1.0,
            )
        ],
    ),
    "medium_duplicate_charge": TaskDefinition(
        task_id="medium_duplicate_charge",
        title="Duplicate charge escalation",
        difficulty="medium",
        instruction=(
            "An enterprise customer reports a duplicate yearly charge. Review the inbox, route the billing issue, "
            "send a reply that acknowledges the duplicate charge and billing review, and place the ticket in the correct status."
        ),
        max_steps=10,
        tickets=[
            TicketSnapshot(
                ticket_id="T-200",
                customer_name="Marco Alvarez",
                subject="We were billed twice for our annual renewal",
                customer_tier="enterprise",
                status="open",
                customer_message=(
                    "Our finance team sees two charges for the same annual renewal. "
                    "Please investigate this duplicate billing issue as soon as possible."
                ),
            ),
            TicketSnapshot(
                ticket_id="T-201",
                customer_name="Ada Brooks",
                subject="Dashboard theme request",
                customer_tier="pro",
                status="open",
                customer_message="Would love more color themes in the dashboard.",
            ),
        ],
        goals=[
            TicketGoal(
                ticket_id="T-200",
                expected_category="billing",
                expected_priority="high",
                expected_team="billing_ops",
                expected_status="pending_customer",
                reply_requirement=ReplyRequirement(
                    description="Reply should mention the duplicate charge and a billing review.",
                    groups=[["duplicate", "billed twice"], ["billing", "finance", "review"]],
                ),
                weight=0.9,
            ),
            TicketGoal(
                ticket_id="T-201",
                expected_status="open",
                weight=0.1,
                required=False,
            ),
        ],
    ),
    "hard_mixed_queue": TaskDefinition(
        task_id="hard_mixed_queue",
        title="Mixed support queue management",
        difficulty="hard",
        instruction=(
            "Process the whole queue. One ticket is a phishing-style security report, one is a production integration bug, "
            "and one is a routine shipping delay. Route each ticket correctly, set the right priority and status, and send replies "
            "tailored to the situation."
        ),
        max_steps=16,
        tickets=[
            TicketSnapshot(
                ticket_id="T-300",
                customer_name="Maya Chen",
                subject="Suspicious login email asking for my password",
                customer_tier="pro",
                status="open",
                customer_message=(
                    "I received an email claiming to be from your support team asking me to confirm my password. "
                    "Is this legitimate? I have not clicked anything yet."
                ),
            ),
            TicketSnapshot(
                ticket_id="T-301",
                customer_name="Leo Fischer",
                subject="Production webhook retries are failing",
                customer_tier="enterprise",
                status="open",
                customer_message=(
                    "Our production webhooks have been failing for two hours after the latest deployment. "
                    "This is blocking order processing for customers."
                ),
            ),
            TicketSnapshot(
                ticket_id="T-302",
                customer_name="Isha Rao",
                subject="Package is two days late",
                customer_tier="standard",
                status="open",
                customer_message=(
                    "My order still shows in transit and missed the delivery window. "
                    "Could you check on the shipment?"
                ),
            ),
        ],
        goals=[
            TicketGoal(
                ticket_id="T-300",
                expected_category="security",
                expected_priority="urgent",
                expected_team="security_response",
                expected_status="escalated",
                reply_requirement=ReplyRequirement(
                    description="Reply should warn the customer not to share credentials and say the security team is investigating.",
                    groups=[["do not share", "don't share", "never share"], ["security", "investigating", "security team"]],
                ),
                weight=0.4,
            ),
            TicketGoal(
                ticket_id="T-301",
                expected_category="bug_report",
                expected_priority="urgent",
                expected_team="engineering",
                expected_status="escalated",
                reply_requirement=ReplyRequirement(
                    description="Reply should mention webhook failure and engineering escalation.",
                    groups=[["webhook", "order processing"], ["engineering", "escalated", "incident"]],
                ),
                weight=0.4,
            ),
            TicketGoal(
                ticket_id="T-302",
                expected_category="shipping",
                expected_priority="normal",
                expected_team="general_support",
                expected_status="resolved",
                reply_requirement=ReplyRequirement(
                    description="Reply should acknowledge the delay and provide a shipment update.",
                    groups=[["delay", "late"], ["shipment", "tracking", "delivery"]],
                ),
                weight=0.2,
            ),
        ],
    ),
}


def get_task(task_id: str) -> TaskDefinition:
    if task_id not in TASKS:
        raise KeyError(f"Unknown task_id '{task_id}'. Available: {', '.join(sorted(TASKS))}")
    return deepcopy(TASKS[task_id])


def list_task_ids() -> list[str]:
    return sorted(TASKS)
