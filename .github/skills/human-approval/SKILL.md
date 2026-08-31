---
name: human-approval
description: Use when a defect recommendation requires human review, production coordination, or business-risk approval.
---

# Human Approval Skill

## Purpose
Define the checkpoints where an agent must stop and request human review.

## Approval Triggers
- Cross-system business logic changes.
- Authentication or authorization changes.
- Data integrity or routing-impacting changes.
- Production configuration updates.
- Low-confidence root-cause analysis.

## Output
- Why approval is needed.
- What decision the human must make.
- What evidence supports the recommendation.
