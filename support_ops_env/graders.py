from __future__ import annotations

from dataclasses import dataclass

from support_ops_env.models import ScoreBreakdown, TicketSnapshot
from support_ops_env.task_bank import TaskDefinition, TicketGoal


EPSILON = 1e-4


@dataclass
class GradeResult:
    score: float
    breakdown: ScoreBreakdown


def _strict_unit_interval(value: float) -> float:
    """Map scores to the open interval (0, 1) for submission validator compliance."""
    if value <= 0.0:
        return EPSILON
    if value >= 1.0:
        return 1.0 - EPSILON
    return value


def _rounded_strict_unit_interval(value: float, ndigits: int = 4) -> float:
    """Round score while preserving strict open-interval bounds."""
    rounded = round(value, ndigits)
    return _strict_unit_interval(rounded)


def _score_reply(reply: str | None, goal: TicketGoal) -> float:
    if goal.reply_requirement is None:
        return 1.0
    if not reply:
        return 0.0

    text = reply.lower()
    matched = 0
    for group in goal.reply_requirement.groups:
        if any(keyword in text for keyword in group):
            matched += 1
    return matched / len(goal.reply_requirement.groups)


def _score_ticket(ticket: TicketSnapshot, goal: TicketGoal) -> tuple[float, list[str], list[str]]:
    earned = 0.0
    possible = 0.0
    completed: list[str] = []
    missing: list[str] = []

    checks = [
        ("category", goal.expected_category, ticket.category),
        ("priority", goal.expected_priority, ticket.priority),
        ("assigned_team", goal.expected_team, ticket.assigned_team),
        ("status", goal.expected_status, ticket.status),
    ]

    for label, expected, actual in checks:
        if expected is None:
            continue
        possible += 1.0
        objective = f"{ticket.ticket_id}:{label}={expected}"
        if actual == expected:
            earned += 1.0
            completed.append(objective)
        else:
            missing.append(objective)

    if goal.reply_requirement is not None:
        possible += 1.0
        reply_score = _score_reply(ticket.latest_reply, goal)
        objective = f"{ticket.ticket_id}:reply"
        earned += reply_score
        if reply_score >= 0.999:
            completed.append(objective)
        else:
            missing.append(objective)

    if possible == 0:
        return 1.0, completed, missing
    return earned / possible, completed, missing


def grade_task(task: TaskDefinition, tickets: list[TicketSnapshot]) -> GradeResult:
    ticket_map = {ticket.ticket_id: ticket for ticket in tickets}
    ticket_scores: dict[str, float] = {}
    completed: list[str] = []
    missing: list[str] = []

    weighted_sum = 0.0
    total_weight = 0.0
    for goal in task.goals:
        ticket = ticket_map[goal.ticket_id]
        ticket_score, done_items, missing_items = _score_ticket(ticket, goal)
        ticket_score = _rounded_strict_unit_interval(_strict_unit_interval(ticket_score), 4)
        ticket_scores[goal.ticket_id] = ticket_score
        weighted_sum += ticket_score * goal.weight
        total_weight += goal.weight
        completed.extend(done_items)
        missing.extend(missing_items)

    aggregate_raw = 0.5 if total_weight == 0 else (weighted_sum / total_weight)
    aggregate_score = _rounded_strict_unit_interval(_strict_unit_interval(aggregate_raw), 4)
    return GradeResult(
        score=aggregate_score,
        breakdown=ScoreBreakdown(
            ticket_scores=ticket_scores,
            aggregate_score=aggregate_score,
            completed_objectives=completed,
            missing_objectives=missing,
        ),
    )
