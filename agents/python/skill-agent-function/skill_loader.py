"""Loads SKILL.md files (frontmatter + body) as prompt sources for the agent.

Resolution order:
1. SKILLS_DIR environment variable, if set (absolute path to a skills root).
2. Bundled ./skills_data (copied in at deploy time by scripts/sync_skills.py).
3. Local dev fallback: walk up from this file to find .github/skills in the
   parent monorepo checkout.
"""
import os
import re

import yaml

_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


class SkillNotFoundError(Exception):
    """Raised when a requested skill name does not exist or is invalid."""


class Skill:
    def __init__(self, name: str, description: str, body: str):
        self.name = name
        self.description = description
        self.body = body


class SkillLoader:
    def __init__(self):
        self._root = self._resolve_skills_root()

    def _resolve_skills_root(self) -> str:
        env_root = os.environ.get("SKILLS_DIR")
        if env_root and os.path.isdir(env_root):
            return env_root

        bundled = os.path.join(os.path.dirname(__file__), "skills_data")
        if os.path.isdir(bundled):
            return bundled

        current = os.path.dirname(os.path.abspath(__file__))
        for _ in range(8):
            candidate = os.path.join(current, ".github", "skills")
            if os.path.isdir(candidate):
                return candidate
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

        raise SkillNotFoundError(
            "No skills directory found. Set SKILLS_DIR or bundle skills_data/."
        )

    def available_skills(self) -> list:
        if not os.path.isdir(self._root):
            return []
        return [
            name
            for name in os.listdir(self._root)
            if os.path.isfile(os.path.join(self._root, name, "SKILL.md"))
        ]

    def load(self, skill_name: str) -> Skill:
        if not skill_name or not _NAME_PATTERN.match(skill_name):
            raise SkillNotFoundError(f"Invalid skill name: {skill_name!r}")

        skill_path = os.path.join(self._root, skill_name, "SKILL.md")
        # Guard against path traversal even though the name pattern already blocks '..' and '/'
        if not os.path.abspath(skill_path).startswith(os.path.abspath(self._root)):
            raise SkillNotFoundError(f"Invalid skill name: {skill_name!r}")
        if not os.path.isfile(skill_path):
            raise SkillNotFoundError(f"Skill not found: {skill_name!r}")

        with open(skill_path, "r", encoding="utf-8") as fh:
            raw = fh.read()

        match = _FRONTMATTER_RE.match(raw)
        if not match:
            raise SkillNotFoundError(f"Skill '{skill_name}' is missing YAML frontmatter.")

        frontmatter = yaml.safe_load(match.group(1)) or {}
        body = match.group(2).strip()

        return Skill(
            name=frontmatter.get("name", skill_name),
            description=frontmatter.get("description", ""),
            body=body,
        )
