"""Trusted task grants; no permission is inferred from MCP tool results."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TaskGrant:
    report_id: str
    email_recipient: str


@dataclass(frozen=True)
class ActionDecision:
    allowed: bool
    reason: str


DEMO_GRANT = TaskGrant(report_id="q3", email_recipient="analyst@example.test")


def authorize_tool_call(
    name: str, arguments: Mapping[str, object], task_grant: TaskGrant
) -> ActionDecision:
    """Allow only known names, exact keys, and task-specific values."""
    if name == "read_report":
        if set(arguments) != {"report_id"}:
            return ActionDecision(False, "INVALID_ARGUMENT_SCHEMA")
        if not isinstance(arguments["report_id"], str):
            return ActionDecision(False, "INVALID_ARGUMENT_SCHEMA")
        if arguments["report_id"] != task_grant.report_id:
            return ActionDecision(False, "REPORT_NOT_GRANTED")
        return ActionDecision(True, "GRANTED")
    if name == "send_email":
        if set(arguments) != {"to", "body"}:
            return ActionDecision(False, "INVALID_ARGUMENT_SCHEMA")
        to, body = arguments["to"], arguments["body"]
        if not isinstance(to, str) or not isinstance(body, str) or not 0 < len(body) <= 10_000:
            return ActionDecision(False, "INVALID_ARGUMENT_SCHEMA")
        if to != task_grant.email_recipient:
            return ActionDecision(False, "RECIPIENT_NOT_GRANTED")
        return ActionDecision(True, "GRANTED")
    return ActionDecision(False, "TOOL_NOT_GRANTED")


Mode = Literal["baseline", "inspect", "full"]
