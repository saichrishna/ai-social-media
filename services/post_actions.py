from __future__ import annotations

APPROVE_BLOCKED_STATUSES = frozenset({
    "scheduled",
    "publishing",
    "published",
    "approved",
})

SCHEDULE_ALLOWED_STATUSES = frozenset({"approved"})


def allowed_actions(status: str | None) -> list[str]:
    normalized = (status or "draft").strip().lower()
    actions: list[str] = ["edit", "regenerate"]

    if normalized not in APPROVE_BLOCKED_STATUSES:
        actions.append("approve")

    if normalized in SCHEDULE_ALLOWED_STATUSES:
        actions.append("schedule")

    order = ["edit", "regenerate", "approve", "schedule"]
    return [action for action in order if action in actions]
