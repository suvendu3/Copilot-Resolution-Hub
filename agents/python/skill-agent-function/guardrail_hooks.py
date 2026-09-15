"""Deterministic pre-LLM hooks for the io-guardrails skill.

Per .github/skills/io-guardrails/SKILL.md, "Layer 0 - Deterministic Pre-LLM
Scope Filter" must run as plain pre-processing code, not a model instruction,
so an off-topic request is rejected without consuming an LLM call or token
budget. This module implements that pre-input hook, plus a symmetrical
deterministic pre-output hook (a regex secret/PII scan) that short-circuits
the LLM-based output guardrail the same way when an obvious secret is present.
"""
import re

SCOPE_ALLOW_PATTERNS = [
    r"\bAB#\d+\b",
    r"\bBUG[-\s]?\d+\b",
    r"\bINT-\d+\b",
    r"\bUSL-\d+\b",
    r"\b(CRM|CCaaS|D365|Dataverse|Azure Function|NICE|Omilia|USL|SOR|MCP)\b",
    r"\b(pipeline|regression|test case|test script|repository|repo|defect|plugin|business rule)\b",
]

SCOPE_REJECT_PATTERNS = [
    r"\b(recipe|cook(ing)?|weather forecast|football score|cricket score|movie recommendation)\b",
    r"\bhow (are|is) (you|your day)\b",
]

CANNED_OUT_OF_SCOPE_RESPONSE = (
    "That question is outside this workspace and my role here as your coding "
    "assistant. I can help with ADO defects, user stories, and CRM / CCaaS / "
    "downstream API analysis in this repository."
)

_SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "aws_access_key"),
    (r"-----BEGIN (RSA |EC )?PRIVATE KEY-----", "private_key"),
    (r"(?i)authorization:\s*bearer\s+[a-z0-9\-_.]+", "bearer_token"),
    (r"(?i)\b(api[_-]?key|secret|password|pwd)\s*[:=]\s*['\"]?[^\s'\"]{6,}", "inline_secret"),
    (r"(?i)Server=.*;.*Password=", "connection_string"),
    (r"\b[A-Za-z0-9]{52}\b", "possible_pat"),  # ADO PATs are 52-char opaque tokens
]


def pre_input_scope_filter(text: str) -> dict:
    """Layer 0 scope filter: decides pass / blocked / uncertain before any LLM call."""
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in SCOPE_REJECT_PATTERNS):
        return {
            "decision": "blocked",
            "stage": "input",
            "check": "pre_llm_scope_filter",
            "reason": "off_topic_reject_list_match",
            "canned_response": CANNED_OUT_OF_SCOPE_RESPONSE,
        }

    if any(re.search(pattern, text, re.IGNORECASE) for pattern in SCOPE_ALLOW_PATTERNS):
        return {"decision": "pass", "stage": "input", "check": "pre_llm_scope_filter", "reason": "allow_list_match"}

    # Uncertain: never hard-block here; let the LLM-based input guardrail decide.
    return {"decision": "uncertain", "stage": "input", "check": "pre_llm_scope_filter", "reason": "no_confident_match"}


def pre_output_secret_scan(text: str) -> dict:
    """Deterministic secret/PII scan that runs before the LLM-based output guardrail."""
    violations = [
        {"check": label, "severity": "block"}
        for pattern, label in _SECRET_PATTERNS
        if re.search(pattern, text)
    ]

    if violations:
        return {
            "decision": "blocked",
            "stage": "output",
            "check": "pre_llm_secret_scan",
            "violations": violations,
        }
    return {"decision": "pass", "stage": "output", "check": "pre_llm_secret_scan", "violations": []}
