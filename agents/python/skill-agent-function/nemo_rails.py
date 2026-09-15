"""NeMo Guardrails (Colang + config.yml) wrapper.

Defense-in-depth layer that complements, not replaces, the regex hooks in
guardrail_hooks.py and the LLM-driven io-guardrails skill checks in graph.py.
Loads guardrails_config/ (config.yml + prompts.yml + rails/*.co).
"""
import os

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.rails.llm.options import GenerationOptions

from guardrail_hooks import pre_input_scope_filter

_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "guardrails_config")

# Must match the "bot refuse to respond" text in guardrails_config/rails/general.co.
REFUSAL_MESSAGE = (
    "That request was blocked by the assistant's safety rails. I can help with "
    "ADO defects, user stories, and CRM / CCaaS / downstream API analysis in "
    "this repository."
)

_rails_instance = None


async def _scope_allow_list_check_action(context: dict = None, **kwargs) -> str:
    user_message = (context or {}).get("user_message", "")
    return pre_input_scope_filter(user_message)["decision"]


def get_rails() -> LLMRails:
    global _rails_instance
    if _rails_instance is None:
        config = RailsConfig.from_path(_CONFIG_DIR)
        for model in config.models:
            if model.type == "main" and model.engine == "azure":
                deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
                if deployment:
                    model.model = deployment
                model.parameters = model.parameters or {}
                model.parameters.setdefault("azure_endpoint", os.environ.get("AZURE_OPENAI_ENDPOINT"))
                model.parameters.setdefault(
                    "api_version", os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
                )
        rails = LLMRails(config)
        rails.register_action(_scope_allow_list_check_action, name="scope_allow_list_check")
        _rails_instance = rails
    return _rails_instance


def _response_text(response) -> str:
    content = getattr(response, "content", None)
    if content is None and isinstance(response, dict):
        content = response.get("content")
    return content or ""


def _was_blocked(response) -> bool:
    return REFUSAL_MESSAGE in _response_text(response)


def check_input(text: str) -> dict:
    """Runs only the input rails (scope allow-list + self check input) on raw text."""
    rails = get_rails()
    response = rails.generate(
        messages=[{"role": "user", "content": text}],
        options=GenerationOptions(rails=["input"]),
    )
    blocked = _was_blocked(response)
    return {"decision": "blocked" if blocked else "pass", "raw": _response_text(response)}


def check_output(candidate_output: str, original_input: str = "") -> dict:
    """Runs only the output rails (self check output) against already-generated text."""
    rails = get_rails()
    response = rails.generate(
        messages=[
            {"role": "user", "content": original_input or "N/A"},
            {"role": "assistant", "content": candidate_output},
        ],
        options=GenerationOptions(rails=["output"]),
    )
    blocked = _was_blocked(response)
    return {"decision": "blocked" if blocked else "pass", "raw": _response_text(response)}
