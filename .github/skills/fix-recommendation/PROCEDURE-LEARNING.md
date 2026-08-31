# Procedure Learning Log for Fix Recommendation Skill

Purpose: capture reusable, verified bug-fix procedures after each validated fix so the skill improves over time.

## Entry Template

Use this template for every new validated bug fix:

```yaml
entry_id: <YYYYMMDD-task-id>
task_id: <bug-id or local-id>
validated_at_utc: <ISO-8601>
domain: CRM | CCaaS | API | other
symptom_pattern: <short pattern>
root_cause_pattern: <short pattern>
minimal_fix_pattern: <short pattern>
unit_test:
  command: <unit test command>
  result: pass | fail | blocked
regression_checks: [<checks>]
references: [<non-sensitive links, file paths, or run IDs>]
```

## Entries

Add new entries at the bottom in chronological order. Do not include secrets, tokens, customer payloads, or credentials.
