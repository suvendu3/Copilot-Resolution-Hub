"""Logfire (OpenTelemetry-native) observability for the skill-agent-function.

Configured once at import. One span per graph node / skill call / guardrail
decision, mirroring the "one span per agent hop/guardrail" model used in
observability/README.md for the markdown-driven agents. Set LOGFIRE_TOKEN as
a Function App setting (or local.settings.json for local dev) - never
hardcode it here. Without a token, spans print to console only (no network
call), so this is safe to import in tests and CI.

Redaction: never attach full LLM prompts/responses as span attributes - only
skill names, decisions, and short flags/lengths. See io-guardrails skill.
"""
import functools
import os

import logfire

logfire.configure(
    token=os.environ.get("LOGFIRE_TOKEN"),
    service_name=os.environ.get("LOGFIRE_SERVICE_NAME", "skill-agent-function"),
    send_to_logfire="if-token-present",
    console=False if os.environ.get("LOGFIRE_TOKEN") else logfire.ConsoleOptions(min_log_level="info"),
)


def _redact(text: str, limit: int = 120) -> str:
    """Never log full skill input/output - only a length-bounded, non-sensitive preview."""
    if not text:
        return ""
    flat = " ".join(str(text).split())
    return flat[:limit] + ("..." if len(flat) > limit else "")


def traced_node(name: str):
    """Wraps a LangGraph node function in a Logfire span named `graph.<name>`."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(state):
            with logfire.span("graph.{node}", node=name):
                result_state = fn(state)
                logfire.info(
                    "graph node completed",
                    node=name,
                    blocked=bool(result_state.get("blocked", False)),
                )
                return result_state

        return wrapper

    return decorator


def traced_skill_call(skill_name: str, preview_text: str = ""):
    """Context manager/span for a single SkillAgent.run() call (one LLM call)."""
    return logfire.span(
        "skill.{skill_name}",
        skill_name=skill_name,
        input_preview=_redact(preview_text),
    )
