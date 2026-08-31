---
name: enterprise-defect-triage
description: Use when reading ADO bugs, user stories, change requests, or requirements to identify the target system and route to the correct agent.
---

# Enterprise Defect Triage Skill

## Purpose
Provide a repeatable workflow for initial defect classification from ADO context.

## Inputs
- ADO Bug ID
- ADO User Story ID
- Change Request
- Requirement

## Checklist
1. Summarize the request in one sentence.
2. Identify the input type: Bug/Defect → proceed to step 3. User Story / Requirement / Change Request → invoke `user-story-validation` skill before step 3; do not route if the story is INCOMPLETE.
3. Extract explicit system names and clues.
4. Classify the request as CRM, CCaaS, or downstream API.
5. Name the likely specialist agent.
6. Note any missing data needed for a confident route.

## Output
- Target system.
- Route decision.
- Confidence level.
- Missing information, if any.
