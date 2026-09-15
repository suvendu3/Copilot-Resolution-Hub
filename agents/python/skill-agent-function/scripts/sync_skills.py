"""Copies .github/skills/*/SKILL.md into skills_data/ for deployment packaging.

Run before `func azure functionapp publish` so the deployed package is
self-contained and does not depend on the monorepo layout at runtime.
"""
import os
import shutil
import sys

FUNCTION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.abspath(os.path.join(FUNCTION_DIR, "..", "..", ".."))
SOURCE = os.path.join(REPO_ROOT, ".github", "skills")
DEST = os.path.join(FUNCTION_DIR, "skills_data")


def main() -> int:
    if not os.path.isdir(SOURCE):
        print(f"Source skills directory not found: {SOURCE}", file=sys.stderr)
        return 1

    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST, exist_ok=True)

    copied = 0
    for name in os.listdir(SOURCE):
        skill_md = os.path.join(SOURCE, name, "SKILL.md")
        if os.path.isfile(skill_md):
            target_dir = os.path.join(DEST, name)
            os.makedirs(target_dir, exist_ok=True)
            shutil.copy2(skill_md, os.path.join(target_dir, "SKILL.md"))
            copied += 1

    print(f"Synced {copied} skill(s) from {SOURCE} to {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
