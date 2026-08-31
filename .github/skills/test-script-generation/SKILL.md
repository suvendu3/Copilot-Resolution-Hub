---
name: test-script-generation
description: Use when generating test scripts after a defect fix or for a new development user story. For defect fixes, locate and run existing test scripts. For new development, auto-generate from acceptance criteria. Integrates with Shankar's test-generation multi-agent.
---

# Test Script Generation Skill

## Purpose
Generate or locate test scripts as part of the fix-recommendation and development workflow. This skill was added following the leadership review on 19 Aug 2026, where Sandip Nikumbha agreed to integrate Shankar's test-script generation multi-agent into this platform.

## When to Invoke
- **After a defect fix recommendation** — locate and validate existing test scripts relevant to the fix.
- **After a new development proposal** — auto-generate test scripts from acceptance criteria.
- Invoked by the Maker Agent as the final step before producing the handoff.

## Mode 1: Defect Fix — Locate Existing Test Scripts

When the input is a bug or defect:

1. From the fix recommendation, identify the affected files and components.
2. Search the repository (using the `docs/repository-registry.md` and `docs/knowledge-base-registry.md` entries) for existing test files covering those components.
   - Preferred locations: `/tests/`, `/test/`, `/spec/`, `__tests__/`, files matching `*.test.*`, `*.spec.*`.
3. List the relevant existing test scripts and their test IDs or names.
4. Identify any gaps: components changed by the fix that have no existing test coverage.
5. Output: existing test list + gap report.

## Mode 2: New Development — Generate Test Scripts

When the input is a user story or new requirement (after passing user-story-validation):

1. Read the acceptance criteria from the enriched ADO work item.
2. For each acceptance criterion, generate a corresponding test case:
   - Test ID (linked to the acceptance criterion).
   - Description (what behaviour is being tested).
   - Pre-conditions.
   - Steps.
   - Expected result.
   - Pass/fail assertion.
3. For each negative/edge scenario in the story, generate a corresponding negative test case.
4. Format: use the project's existing test format if discoverable from the repository; otherwise use structured plain-text test cases.

## Mode 3: CRM (Playwright + TypeScript)

Use this mode when the affected system is CRM (D365 / Contact360 / Service360). The authoritative test framework is the `automation-scripts` repository (`GSH-CRM`, branch `enh-automation`) — see `docs/repository-registry.md` and `docs/knowledge-base-registry.md`. Resolve that repository locally before generating; do not invent a new framework.

1. **Bind to the framework conventions** by reading, in order:
   - `playwright.config.ts`, `package.json` (test scripts), `lib/config/env.ts` (environments).
   - `pages/` (page objects), `lib/api/` (typed `USLApiClient`), `fixtures/` (`auth`, `apiContext`), `data/*.xlsx` (test data).
   - Existing specs closest to the change to copy structure and naming.
2. **Choose the layer:**
   - Service/data-shape change → add an API spec under `tests/API/` reusing `USLApiClient` (fast, headless, deterministic — preferred gate).
   - UI/behaviour change → add a UI E2E spec reusing existing page objects.
3. **Name the file** `TC-<ADO test case id>_<ShortName>.spec.ts`, one `test.describe` per acceptance criterion, positive + negative cases, tied to the AC / INT id.
4. **Do not hardcode secrets or environment URLs** — use the existing env/fixture/variable-group mechanism.
5. **Run command:** `npm run test:dev` (API/smoke subset) or the environment-specific script (`test:sit`, `test:qa`). Report pass/fail.

### Dev→SIT Quality Gate (CRM)
- A CRM code change is promoted from **CRM Dev to CRM SIT only after** the CRM Playwright gate suite passes against CRM Dev.
- Gate suite = `tests/API` + `tests/Smoke` (fast, deterministic). Full `tests/Regression` runs post-promotion.
- The gate can run agent-driven (Maker→Checker executes the specs and the Checker verdict is the gate) or via the gating pipeline — the pipeline is optional.
- If the gate suite cannot execute (environment down, credentials expired, skipped specs), return `blocked` with evidence rather than passing.

## Output Format

```
Test Script Generation Report
──────────────────────────────
Work Item:    <ADO ID>
Mode:         DEFECT FIX | NEW DEVELOPMENT
Component(s): <affected files or modules>

--- Existing Test Scripts (Defect Fix mode) ---
  <test file path>  →  <test name / ID>
  ...

--- Gaps (components with no existing test coverage) ---
  <component>  →  no test coverage found

--- Generated Test Cases (New Development mode) ---
  TC-01: <acceptance criterion reference>
    Description:    <what is tested>
    Pre-conditions: <state before test>
    Steps:          <numbered steps>
    Expected:       <expected outcome>
    Assertion:      PASS if <condition>

  TC-02: <edge case or negative scenario>
    ...

--- Recommendation ---
  <Run existing tests with: npm test / pytest / dotnet test / etc.>
  <New test cases to be added to: <suggested test file path>>
```

## Rules
- Do not invent test cases for acceptance criteria that do not exist in the story.
- Do not modify existing test scripts — only locate and reference them.
- If no test framework or existing test structure is found, note it as a gap and recommend the appropriate framework for the stack.
- Generated test cases must be tied to specific acceptance criteria or scenarios from the ADO work item.
- This skill runs after the fix recommendation is formed; it does not replace unit test execution (that remains in `fix-recommendation/SKILL.md`).

## Integration Note
This skill is designed to eventually incorporate Shankar's test-script generation multi-agent output. When that integration is complete:
- Point this skill to Shankar's agent as the generation engine.
- Shankar's agent output feeds into this skill's output format.
- The Maker Agent remains the orchestrator; Shankar's agent is a sub-capability.
