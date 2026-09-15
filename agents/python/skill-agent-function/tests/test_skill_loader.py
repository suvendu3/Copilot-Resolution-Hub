import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from skill_loader import SkillLoader, SkillNotFoundError


def test_loads_enterprise_defect_triage():
    loader = SkillLoader()
    skill = loader.load("enterprise-defect-triage")
    assert skill.name == "enterprise-defect-triage"
    assert "Checklist" in skill.body


def test_rejects_path_traversal():
    loader = SkillLoader()
    with pytest.raises(SkillNotFoundError):
        loader.load("../../etc/passwd")


def test_rejects_unknown_skill():
    loader = SkillLoader()
    with pytest.raises(SkillNotFoundError):
        loader.load("does-not-exist")


def test_available_skills_lists_known_entries():
    loader = SkillLoader()
    skills = loader.available_skills()
    assert "enterprise-defect-triage" in skills
    assert "fix-recommendation" in skills
