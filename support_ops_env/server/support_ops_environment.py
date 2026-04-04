from __future__ import annotations

from copy import deepcopy
from typing import Any

from support_ops_env.graders import grade_task
from support_ops_env.models import SupportOpsAction, SupportOpsObservation, SupportOpsState, TicketSnapshot
from support_ops_env.openenv_compat import StepResult
from support_ops_env.task_bank import get_task, list_task_ids


class SupportOpsEnvironment:
    """Deterministic customer support operations simulator."""

    def __init__(self) -> None:
        self._task = get_task("easy_password_reset")
        self._tickets = deepcopy(self._task.tickets)
        self._active_ticket_id: str | None = None
        self._step_count = 0
        self._action_history: list[str] = []
        self._recent_events: list[str] = ["Environment initialized."]
        self._done = False
        self._last_score = grade_task(self._task, self._tickets).score

    def reset(self, task_id: str | None = None) -> SupportOpsObservation:
        if task_id is None:
            task_id = "easy_password_reset"
        self._task = get_task(task_id)
        self._tickets = deepcopy(self._task.tickets)
        self._active_ticket_id = None
        self._step_count = 0
        self._action_history = []
        self._recent_events = [f"Loaded task '{self._task.title}'. Available tasks: {', '.join(list_task_ids())}"]
        self._done = False
        self._last_score = grade_task(self._task, self._tickets).score
        return self._make_observation()

    def state(self) -> SupportOpsState:
        grade = grade_task(self._task, self._tickets)
        return SupportOpsState(
            task_id=self._task.task_id,
            step_count=self._step_count,
            max_steps=self._task.max_steps,
            active_ticket_id=self._active_ticket_id,
            tickets=[ticket.model_copy(deep=True) for ticket in self._tickets],
            score_breakdown=grade.breakdown,
            action_history=list(self._action_history),
        )

    def step(self, action: SupportOpsAction) -> StepResult[SupportOpsObservation]:
        if self._done:
            observation = self._make_observation(done=True)
            return StepResult(observation=observation, reward=-0.05, done=True, info={"error": "Episode already finished."})

        self._step_count += 1
        reward = -0.01
        info: dict[str, Any] = {"task_id": self._task.task_id}
        action_summary = self._summarize_action(action)
        self._action_history.append(action_summary)

        try:
            reward += self._apply_action(action)
        except ValueError as exc:
            reward -= 0.1
            self._recent_events = [str(exc)]
            info["error"] = str(exc)

        grade = grade_task(self._task, self._tickets)
        delta = grade.score - self._last_score
        reward += round(delta, 4)
        self._last_score = grade.score
        info["score"] = grade.score
        info["score_breakdown"] = grade.breakdown.model_dump()

        if action.action_type == "submit_task":
            self._done = True
            reward += 0.1 if grade.score >= 0.8 else -0.1

        if self._step_count >= self._task.max_steps:
            self._done = True
            reward -= 0.15
            self._recent_events = [f"Maximum steps reached ({self._task.max_steps})."]

        observation = self._make_observation(done=self._done)
        return StepResult(observation=observation, reward=round(reward, 4), done=self._done, info=info)

    def _apply_action(self, action: SupportOpsAction) -> float:
        if action.action_type == "list_tickets":
            self._recent_events = [f"Queue contains {len(self._tickets)} tickets."]
            return 0.0

        if action.action_type == "noop":
            self._recent_events = ["No-op executed."]
            return -0.03

        if action.action_type == "submit_task":
            self._recent_events = ["Task submitted for grading."]
            return 0.0

        ticket = self._require_ticket(action.ticket_id)

        if action.action_type == "open_ticket":
            self._active_ticket_id = ticket.ticket_id
            self._recent_events = [f"Opened {ticket.ticket_id}: {ticket.subject}"]
            return 0.0

        if action.action_type == "classify_ticket":
            if action.category is None or action.priority is None:
                raise ValueError("classify_ticket requires both category and priority.")
            ticket.category = action.category
            ticket.priority = action.priority
            self._recent_events = [f"Updated {ticket.ticket_id} classification to {action.category}/{action.priority}."]
            return 0.02

        if action.action_type == "assign_ticket":
            if action.team is None:
                raise ValueError("assign_ticket requires team.")
            ticket.assigned_team = action.team
            self._recent_events = [f"Assigned {ticket.ticket_id} to {action.team}."]
            return 0.02

        if action.action_type == "reply_ticket":
            if not action.message:
                raise ValueError("reply_ticket requires a customer-facing message.")
            ticket.latest_reply = action.message.strip()
            self._recent_events = [f"Replied to {ticket.ticket_id}."]
            return 0.03

        if action.action_type == "set_status":
            if action.status is None:
                raise ValueError("set_status requires status.")
            ticket.status = action.status
            self._recent_events = [f"Set {ticket.ticket_id} status to {action.status}."]
            return 0.02

        raise ValueError(f"Unsupported action_type '{action.action_type}'.")

    def _require_ticket(self, ticket_id: str | None) -> TicketSnapshot:
        if not ticket_id:
            raise ValueError("This action requires ticket_id.")
        for ticket in self._tickets:
            if ticket.ticket_id == ticket_id:
                return ticket
        raise ValueError(f"Unknown ticket_id '{ticket_id}'.")

    def _make_observation(self, done: bool = False) -> SupportOpsObservation:
        grade = grade_task(self._task, self._tickets)
        active_ticket = next((ticket for ticket in self._tickets if ticket.ticket_id == self._active_ticket_id), None)
        queue_overview = [
            f"{ticket.ticket_id} | {ticket.subject} | tier={ticket.customer_tier} | status={ticket.status}"
            for ticket in self._tickets
        ]
        return SupportOpsObservation(
            task_id=self._task.task_id,
            task_title=self._task.title,
            instruction=self._task.instruction,
            queue_overview=queue_overview,
            active_ticket=active_ticket.model_copy(deep=True) if active_ticket else None,
            recent_events=list(self._recent_events),
            progress_score=grade.score,
            remaining_steps=max(self._task.max_steps - self._step_count, 0),
            done=done,
        )

    @staticmethod
    def _summarize_action(action: SupportOpsAction) -> str:
        fields = [f"type={action.action_type}"]
        for key in ("ticket_id", "category", "priority", "team", "status"):
            value = getattr(action, key)
            if value is not None:
                fields.append(f"{key}={value}")
        if action.message:
            fields.append(f"message={action.message[:60]}")
        return " | ".join(fields)
