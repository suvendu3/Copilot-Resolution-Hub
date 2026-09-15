"""LangGraph-based agentic flow chaining multiple SKILL.md procedures.

Flow: pre-input hook (deterministic regex) -> NeMo Guardrails input rails
(Colang) -> input guardrails (LLM skill) -> defect triage -> fix
recommendation -> pre-output hook (deterministic regex) -> NeMo Guardrails
output rail (Colang) -> output guardrails (LLM skill). Each guard layer can
short-circuit the graph before the next, more expensive layer runs, per the
io-guardrails skill's Layer 0 requirement and defense-in-depth practice.
This graph lives only in this standalone add-on service; it does not change
the native Copilot markdown-driven architecture in the rest of the repo.
"""
from typing import TypedDict

from langgraph.graph import END, StateGraph

import nemo_rails
import observability
from agent import SkillAgent
from guardrail_hooks import pre_input_scope_filter, pre_output_secret_scan
from skill_loader import SkillLoader

_loader = SkillLoader()
_agent_cache: dict = {}


def _get_agent(skill_name: str) -> SkillAgent:
    if skill_name not in _agent_cache:
        _agent_cache[skill_name] = SkillAgent(skill_name, loader=_loader)
    return _agent_cache[skill_name]


class SkillGraphState(TypedDict, total=False):
    input: str
    context: dict
    pre_input_hook: dict
    nemo_input_check: dict
    guardrail_input: dict
    triage: dict
    fix_recommendation: dict
    pre_output_hook: dict
    nemo_output_check: dict
    guardrail_output: dict
    final_output: object
    blocked: bool
    error: str


def _decision_of(node_result: dict) -> str:
    output = node_result.get("output")
    if isinstance(output, dict):
        return str(output.get("decision", "")).lower()
    return ""


def _node_pre_input_hook(state: SkillGraphState) -> SkillGraphState:
    """Layer 0: deterministic scope filter, runs before any LLM call."""
    result = pre_input_scope_filter(state["input"])
    state["pre_input_hook"] = result
    if result["decision"] == "blocked":
        state["blocked"] = True
        state["error"] = result["canned_response"]
    return state


_node_pre_input_hook = observability.traced_node("pre_input_hook")(_node_pre_input_hook)


def _route_after_pre_input_hook(state: SkillGraphState) -> str:
    return "blocked" if state.get("blocked") else "continue"


def _node_nemo_input_check(state: SkillGraphState) -> SkillGraphState:
    """Colang-driven layer: NeMo Guardrails input rails (scope filter + self check input)."""
    result = nemo_rails.check_input(state["input"])
    state["nemo_input_check"] = result
    if result["decision"] == "blocked":
        state["blocked"] = True
        state["error"] = "Input blocked by NeMo Guardrails input rails."
    return state


_node_nemo_input_check = observability.traced_node("nemo_input_check")(_node_nemo_input_check)


def _route_after_nemo_input_check(state: SkillGraphState) -> str:
    return "blocked" if state.get("blocked") else "continue"


def _node_input_guardrails(state: SkillGraphState) -> SkillGraphState:
    result = _get_agent("io-guardrails").run(state["input"], context=state.get("context", {}))
    state["guardrail_input"] = result
    if _decision_of(result) == "blocked":
        state["blocked"] = True
        state["error"] = "Input blocked by io-guardrails."
    return state


_node_input_guardrails = observability.traced_node("input_guardrails")(_node_input_guardrails)


def _node_triage(state: SkillGraphState) -> SkillGraphState:
    result = _get_agent("enterprise-defect-triage").run(state["input"], context=state.get("context", {}))
    state["triage"] = result
    return state


_node_triage = observability.traced_node("triage")(_node_triage)


def _node_fix_recommendation(state: SkillGraphState) -> SkillGraphState:
    context = dict(state.get("context", {}))
    context["triage_result"] = state.get("triage", {}).get("output")
    result = _get_agent("fix-recommendation").run(state["input"], context=context)
    state["fix_recommendation"] = result
    return state


_node_fix_recommendation = observability.traced_node("fix_recommendation")(_node_fix_recommendation)


def _node_pre_output_hook(state: SkillGraphState) -> SkillGraphState:
    """Deterministic secret/PII scan, runs before the LLM-based output guardrail."""
    candidate = state.get("fix_recommendation", {}).get("raw_output", "")
    result = pre_output_secret_scan(candidate)
    state["pre_output_hook"] = result
    if result["decision"] == "blocked":
        state["blocked"] = True
        state["error"] = "Output blocked by deterministic secret scan (pre_llm_secret_scan)."
    return state


_node_pre_output_hook = observability.traced_node("pre_output_hook")(_node_pre_output_hook)


def _route_after_pre_output_hook(state: SkillGraphState) -> str:
    return "blocked" if state.get("blocked") else "continue"


def _node_nemo_output_check(state: SkillGraphState) -> SkillGraphState:
    """Colang-driven layer: NeMo Guardrails output rail (self check output)."""
    candidate = state.get("fix_recommendation", {}).get("raw_output", "")
    result = nemo_rails.check_output(candidate, original_input=state["input"])
    state["nemo_output_check"] = result
    if result["decision"] == "blocked":
        state["blocked"] = True
        state["error"] = "Output blocked by NeMo Guardrails output rail."
    return state


_node_nemo_output_check = observability.traced_node("nemo_output_check")(_node_nemo_output_check)


def _route_after_nemo_output_check(state: SkillGraphState) -> str:
    return "blocked" if state.get("blocked") else "continue"


def _node_output_guardrails(state: SkillGraphState) -> SkillGraphState:
    candidate = state.get("fix_recommendation", {}).get("raw_output", "")
    result = _get_agent("io-guardrails").run(candidate, context={"stage": "output"})
    state["guardrail_output"] = result
    if _decision_of(result) == "blocked":
        state["blocked"] = True
        state["error"] = "Output blocked by io-guardrails."
    else:
        state["final_output"] = state.get("fix_recommendation", {}).get("output")
    return state


_node_output_guardrails = observability.traced_node("output_guardrails")(_node_output_guardrails)


def _route_after_input_guardrails(state: SkillGraphState) -> str:
    return "blocked" if state.get("blocked") else "continue"


def build_graph():
    graph = StateGraph(SkillGraphState)
    graph.add_node("pre_input_hook", _node_pre_input_hook)
    graph.add_node("nemo_input_check", _node_nemo_input_check)
    graph.add_node("input_guardrails", _node_input_guardrails)
    graph.add_node("triage", _node_triage)
    graph.add_node("fix_recommendation", _node_fix_recommendation)
    graph.add_node("pre_output_hook", _node_pre_output_hook)
    graph.add_node("nemo_output_check", _node_nemo_output_check)
    graph.add_node("output_guardrails", _node_output_guardrails)

    graph.set_entry_point("pre_input_hook")
    graph.add_conditional_edges(
        "pre_input_hook",
        _route_after_pre_input_hook,
        {"blocked": END, "continue": "nemo_input_check"},
    )
    graph.add_conditional_edges(
        "nemo_input_check",
        _route_after_nemo_input_check,
        {"blocked": END, "continue": "input_guardrails"},
    )
    graph.add_conditional_edges(
        "input_guardrails",
        _route_after_input_guardrails,
        {"blocked": END, "continue": "triage"},
    )
    graph.add_edge("triage", "fix_recommendation")
    graph.add_edge("fix_recommendation", "pre_output_hook")
    graph.add_conditional_edges(
        "pre_output_hook",
        _route_after_pre_output_hook,
        {"blocked": END, "continue": "nemo_output_check"},
    )
    graph.add_conditional_edges(
        "nemo_output_check",
        _route_after_nemo_output_check,
        {"blocked": END, "continue": "output_guardrails"},
    )
    graph.add_edge("output_guardrails", END)

    return graph.compile()


def run_graph(user_input: str, context: dict = None) -> SkillGraphState:
    app = build_graph()
    initial_state: SkillGraphState = {"input": user_input, "context": context or {}}
    return app.invoke(initial_state)
