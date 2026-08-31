---
name: fix-recommendation
description: Use when turning defect evidence into code-fix recommendations, affected files, and validation steps.
---

# Fix Recommendation Skill

## Purpose
Standardize the final recommendation produced by specialist and domain agents.

## Required Sections
- Problem summary.
- Suspected root cause.
- Recommended fix.
- Affected files or components.
- Tests to run.
- Risk and rollback considerations.

## Unit Test Gate (Bug Fix)
- A bug-fix recommendation is complete only after repository unit tests pass.
- Include explicit unit test commands in the validation section.
- If unit tests cannot be identified or executed, mark the recommendation as blocked and report the reason.

Recommended command discovery order:
1. Repository-specific documented test command.
2. Language standard command from repository metadata.
3. Fallback command set with clear evidence of attempted execution.

Common examples by stack:
- JavaScript or TypeScript: `npm test` or `pnpm test`.
- Python: `pytest`.
- .NET: `dotnet test`.
- Java: `mvn test` or `gradle test`.
- Go: `go test ./...`.

## Procedure Learning Injection
- After each validated bug fix, write one reusable, non-sensitive procedure lesson to `.github/skills/fix-recommendation/PROCEDURE-LEARNING.md`.
- Each lesson must include:
	- Task or bug identifier.
	- Symptom pattern.
	- Root-cause pattern.
	- Minimal fix pattern.
	- Unit test command and result.
	- Regression checks.
- Keep entries concise and implementation-oriented so future fixes can reuse them.

## Test Script Generation (added 19 Aug 2026)
After producing the fix recommendation, invoke the `test-script-generation` skill:
- **Defect fix:** locate existing test scripts covering the changed components. List them and identify any gaps in test coverage.
- **New development:** generate test cases from the acceptance criteria in the user story (requires `user-story-validation` to have passed first).
Include the test script results in the final recommendation output under a dedicated "Test Coverage" section.

## Quality Bar
- Recommend the smallest safe fix.
- Prefer targeted changes over broad refactors.
- Tie every recommendation back to evidence.
- Promote only procedure lessons that are verified and safe to reuse.
