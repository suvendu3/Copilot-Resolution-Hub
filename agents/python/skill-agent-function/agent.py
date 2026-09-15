"""SkillAgent: executes a SKILL.md's instructions against a given input via an LLM."""
import json

import llm_client
import observability
from skill_loader import SkillLoader

_SYSTEM_TEMPLATE = """You are an automation agent executing a documented skill procedure.

Skill name: {name}
Skill description: {description}

Follow the skill instructions below exactly. Respond with a single JSON object only,
no markdown fences, containing your findings structured to match the skill's
documented Output/Required Sections where applicable.

--- SKILL INSTRUCTIONS ---
{body}
--- END SKILL INSTRUCTIONS ---
"""


class SkillAgent:
    def __init__(self, skill_name: str, loader: SkillLoader = None):
        self._loader = loader or SkillLoader()
        self.skill = self._loader.load(skill_name)

    def _system_prompt(self) -> str:
        return _SYSTEM_TEMPLATE.format(
            name=self.skill.name,
            description=self.skill.description,
            body=self.skill.body,
        )

    def run(self, user_input: str, context: dict = None) -> dict:
        context = context or {}
        user_message = user_input
        if context:
            user_message = f"{user_input}\n\nAdditional context:\n{json.dumps(context)}"

        with observability.traced_skill_call(self.skill.name, user_input):
            raw_output = llm_client.chat(self._system_prompt(), user_message)

        parsed = None
        try:
            parsed = json.loads(raw_output)
        except (json.JSONDecodeError, TypeError):
            parsed = None

        return {
            "skill": self.skill.name,
            "raw_output": raw_output,
            "output": parsed if parsed is not None else raw_output,
        }
