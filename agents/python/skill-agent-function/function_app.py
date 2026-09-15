"""Azure Function entry point: standalone HTTP-triggered skill executor.

This service is independent of the native Copilot multi-agent architecture
(.github/agents, .github/skills consumed directly by Copilot). It loads the
same SKILL.md files as its prompt source and executes them via an LLM call,
so it can run unattended in CI/CD or other automation contexts.
"""
import json
import logging

import azure.functions as func
import logfire

import observability  # noqa: F401 - configures Logfire on import
from agent import SkillAgent
from graph import run_graph
from skill_loader import SkillLoader, SkillNotFoundError

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

_loader = SkillLoader()


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok", "skills": sorted(_loader.available_skills())}),
        mimetype="application/json",
    )


@app.route(route="execute-skill", methods=["POST"])
def execute_skill(req: func.HttpRequest) -> func.HttpResponse:
    with logfire.span("http.execute_skill"):
        try:
            body = req.get_json()
        except ValueError:
            return _error(400, "Request body must be valid JSON.")

        skill_name = body.get("skill")
        user_input = body.get("input")
        context = body.get("context", {})

        if not skill_name or not isinstance(skill_name, str):
            return _error(400, "Field 'skill' is required and must be a string.")
        if not user_input or not isinstance(user_input, str):
            return _error(400, "Field 'input' is required and must be a string.")
        if not isinstance(context, dict):
            return _error(400, "Field 'context' must be an object if provided.")

        logfire.info("execute-skill requested", skill=skill_name)

        try:
            agent = SkillAgent(skill_name, loader=_loader)
        except SkillNotFoundError as exc:
            return _error(404, str(exc))

        try:
            result = agent.run(user_input, context=context)
        except Exception:  # noqa: BLE001 - never leak internals to the caller
            logging.exception("Skill execution failed for skill=%s", skill_name)
            return _error(502, "Skill execution failed. See function logs for details.")

        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200,
        )


def _error(status_code: int, message: str) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"error": message}),
        mimetype="application/json",
        status_code=status_code,
    )


@app.route(route="execute-graph", methods=["POST"])
def execute_graph(req: func.HttpRequest) -> func.HttpResponse:
    with logfire.span("http.execute_graph"):
        try:
            body = req.get_json()
        except ValueError:
            return _error(400, "Request body must be valid JSON.")

        user_input = body.get("input")
        context = body.get("context", {})

        if not user_input or not isinstance(user_input, str):
            return _error(400, "Field 'input' is required and must be a string.")
        if not isinstance(context, dict):
            return _error(400, "Field 'context' must be an object if provided.")

        try:
            final_state = run_graph(user_input, context=context)
        except Exception:  # noqa: BLE001 - never leak internals to the caller
            logging.exception("Graph execution failed")
            return _error(502, "Graph execution failed. See function logs for details.")

        return func.HttpResponse(
            json.dumps(dict(final_state)),
            mimetype="application/json",
            status_code=200,
        )

