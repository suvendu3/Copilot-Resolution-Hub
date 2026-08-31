---
name: system-routing
description: Use when choosing between CRM, CCaaS, and downstream API agents or between a domain and sub-agent.
---

# System Routing Skill

## Purpose
Encode the routing map so future teams can change behavior by editing markdown instead of code.

## Routing Rules
- CRM -> CRM Agent.
- D365, Dataverse, plugin, entity, business rule -> D365 Agent.
- Azure Function, binding, deployment, integration -> Azure Function Agent.
- CCaaS -> CCaaS Agent.
- NICE, routing, IVR, queue, script -> NICE Agent.
- Omilia, intent, NLU, entity, dialogue -> OMILIA Agent.
- API, integration, dependency, backend -> API Agent.
- USL -> USL Agent.
- SOR -> SOR Agent.

## Output
- Primary agent.
- Secondary agent, if needed.
- Reason for selection.
