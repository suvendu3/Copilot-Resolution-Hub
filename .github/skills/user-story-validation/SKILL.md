---
name: user-story-validation
description: Use when a user story, change request, or requirement is submitted to validate completeness before routing it to a domain agent. Checks that acceptance criteria, scenarios, and scope are defined.
---

# User Story Validation Skill

## Purpose
Validate the completeness of a user story or requirement before the Supervisor Agent routes it to a domain agent. Incomplete stories produce ambiguous recommendations. This skill gates routing on a minimum quality bar.

## When to Invoke
- Input is a User Story ID, change request, or new requirement (not a bug/defect).
- Invoked by the Supervisor Agent immediately after ADO enrichment and before domain routing.

## Validation Checklist

Run all checks against the enriched ADO work item. Report the result for each.

### 1. Acceptance Criteria
- [ ] At least one acceptance criterion is defined.
- [ ] Each criterion is testable (can be confirmed true or false).
- [ ] No criterion is ambiguous or purely descriptive (e.g., "the system should be fast" without a measurable threshold).

### 2. Scenarios
- [ ] At least one positive (happy-path) scenario is described.
- [ ] At least one negative or edge-case scenario is described.
- [ ] Scenarios reference the affected system or component explicitly.

### 3. Scope Clarity
- [ ] The story identifies the target system (CRM, CCaaS, or API) — explicitly or by inference.
- [ ] The story does not span multiple domains without a defined integration point.
- [ ] Out-of-scope items are explicitly listed if the story is a subset of a larger feature.

### 4. Dependencies
- [ ] Dependent stories, tickets, or external systems are referenced if applicable.
- [ ] Blocking dependencies are flagged as such.

### 5. Definition of Done
- [ ] A definition of done or a completion condition is stated or can be inferred from acceptance criteria.

## Output Format

Return a structured completeness report before routing proceeds:

```
User Story Completeness Report
──────────────────────────────
Story ID:         <ADO ID>
Title:            <story title>
Overall status:   COMPLETE | INCOMPLETE | BLOCKED

Acceptance Criteria:   PASS | FAIL — <detail>
Scenarios:             PASS | FAIL — <detail>
Scope Clarity:         PASS | FAIL — <detail>
Dependencies:          PASS | FAIL — <detail>
Definition of Done:    PASS | FAIL — <detail>

Gaps identified:
  - <specific missing item 1>
  - <specific missing item 2>

Recommended action:
  - COMPLETE   → proceed to domain routing
  - INCOMPLETE → return gaps to the requester; do not route until resolved
  - BLOCKED    → escalate to human approver with blocking reason
```

## Rules
- Do not route an INCOMPLETE story to a domain agent. Return the gaps to the requester.
- Do not invent acceptance criteria or scenarios. If they are missing, report them as missing.
- A BLOCKED status (dependency cannot be resolved by the requester) requires human approval before proceeding.
- If the story is COMPLETE, append the completeness report to the Supervisor routing output as a quality record.
