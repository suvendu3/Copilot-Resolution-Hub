# Repository Documentation Audit

**Review date:** 2026-09-15  
**Scope:** Repository documentation, Markdown agents and skills, Python Azure Function add-on, MCP configuration, observability, pipelines, tests, and governance records.

## Executive Summary

The repository contains strong architecture, governance, agent, skill, and observability material. The main weakness is operational documentation: a new contributor can understand the intended design, but cannot yet follow one complete, authoritative path to install, configure, run, troubleshoot, secure, and deploy every supported execution mode.

The highest-priority documentation work is:

1. Add a local setup and verification guide.
2. Add a guide for invoking and interpreting the native Copilot agents.
3. Document the distinction between the native Markdown workflow and the separate Python Azure Function add-on.
4. Add production deployment and security runbooks.
5. Complete or clearly disposition the pending MCP and knowledge-base records.

## Findings

### High Priority: Missing Operational Documentation

#### 1. Local setup and onboarding guide

There is no single setup guide covering:

- Required VS Code and GitHub Copilot mode.
- Python and Azure Functions Core Tools setup.
- `uv` installation and the Python add-on environment.
- PAC CLI prerequisites and authentication.
- `.vscode/mcp.json` inputs and safe credential handling.
- How to verify each MCP connection.
- A minimal smoke test for the native agent path and the Python Function path.

Relevant implementation references:

- [README1.md](../README1.md)
- [Skill Agent Function README](../agents/python/skill-agent-function/README.md)
- [MCP configuration](../.vscode/mcp.json)
- [Observability README](../observability/README.md)

**Recommended document:** `docs/setup.md`.

#### 2. Agent invocation and user runbook

The current live demo explains one prompt, but does not provide a complete user runbook. It should explain:

- How to switch GitHub Copilot Chat to Agent mode.
- Which prompt starts Supervisor routing.
- How to use domain or specialist agents directly when appropriate.
- What to provide when routing is ambiguous.
- How to read the Maker handoff and Checker verdict.
- What `validated`, `rejected`, `blocked`, and `needs_human_approval` mean.
- How to recover from missing evidence or an unavailable MCP.

Relevant references:

- [Enterprise bug prompts](enterprise-bug-end-to-end-prompts.md)
- [End-to-end flow](end-to-end-flow.md)
- [Supervisor Agent](../.github/agents/supervisor-agent.md)
- [Checker Agent](../.github/agents/checker-agent.md)

**Recommended document:** `docs/running-agents.md`.

#### 3. Deployment and environment runbook

The repository has a target deployment diagram and Python Function deployment commands, but no unified deployment procedure. Missing topics include:

- Local versus centrally hosted MCP topology.
- Azure Function provisioning and required runtime settings.
- Key Vault references and function-key rotation.
- APIM or Front Door placement for external callers.
- Azure Entra ID token validation for a future central gateway.
- Network controls, monitoring, alerting, rollback, and incident response.
- Promotion from development to SIT and production.

Relevant references:

- [Copilot instructions](../copilot-instructions.md)
- [Skill Agent Function README](../agents/python/skill-agent-function/README.md)
- [Target deployment architecture](target-deployment-architecture.mmd)
- [CRM development gate](pipelines/azure-pipelines-crm-dev-gate.yml)

**Recommended document:** `docs/deployment.md`.

#### 4. Security and compliance runbook

Security rules are distributed across the I/O guardrails, MCP governance, `.gitignore`, and AI governance documents. There is no single security runbook that explains the operational controls and their owners.

Document at least:

- Secret and PAT storage, rotation, and revocation.
- Read-only MCP identity requirements.
- Prompt-injection and data-exfiltration threat scenarios.
- Redaction verification for logs and telemetry.
- Omilia MCP restrictions and the approved interim workaround.
- Access review and incident response.
- Data classification, telemetry retention, residency, and deletion.
- Security scanning and release gates.

The AI governance file explicitly leaves telemetry retention to be ratified by the owner, so this should be tracked as a policy decision rather than presented as complete.

Relevant references:

- [I/O guardrails](../.github/skills/io-guardrails/SKILL.md)
- [MCP governance](../.github/skills/mcp-governance/SKILL.md)
- [MCP inspection inventory](mcp-inspection-inventory.md)
- [AI governance](ai-governance.md)
- [Human approval](../.github/skills/human-approval/SKILL.md)

**Recommended documents:** `docs/security.md` and `docs/compliance.md`.

#### 5. Troubleshooting and FAQ

There is no decision-oriented troubleshooting guide for common failures such as:

- PAC CLI or Function Core Tools not found.
- MCP authentication failure or expired PAT.
- MCP server configured but still marked `pending`.
- Ambiguous domain routing.
- Incomplete user-story input.
- Azure OpenAI configuration failure.
- Function key or HTTP authorization failure.
- Logfire or OTLP export failure.
- Secret scan or output-grounding rejection.
- Missing test environment variables or stale test data.

**Recommended document:** `docs/troubleshooting.md` with short decision trees and links to the relevant logs or configuration files.

### High Priority: Architecture and Readiness Gaps

#### 6. Native Markdown workflow versus Python add-on

The canonical instructions state that there is no Python orchestration, LangGraph, or custom routing source code. Separately, `agents/python/skill-agent-function/` contains a working LangGraph-based Azure Function with HTTP endpoints, NeMo Guardrails, and Logfire instrumentation.

The Python README correctly says that this is an independent add-on, but the relationship is not documented from the repository entry point. Add a deployment-mode comparison covering:

| Mode | Runtime | Invocation | Best for |
| --- | --- | --- | --- |
| Native Copilot | VS Code GitHub Copilot Agent mode | Copilot Chat | Interactive governed investigation |
| Skill Agent Function | Azure Functions + LangGraph | HTTP API | Unattended CI/CD, scheduled jobs, and external callers |

The comparison must state that the two paths share skill files but do not share the same runtime orchestration, approval behavior, or evidence integrations.

Relevant references:

- [Global operating rules](../copilot-instructions.md)
- [Skill Agent Function README](../agents/python/skill-agent-function/README.md)
- [Function entry point](../agents/python/skill-agent-function/function_app.py)
- [LangGraph flow](../agents/python/skill-agent-function/graph.py)

**Recommended location:** add a `Deployment Modes` section to [README1.md](../README1.md) and [copilot-instructions.md](../copilot-instructions.md), with a link to the Function README.

#### 7. MCP inspection inventory is incomplete

The MCP inventory marks `pac-mcp`, its fallbacks, and `ado-remote-mcp` as `pending`, while the operating instructions describe PAC MCP usage. The approved tool inventory is still a template, and future D365, Azure, USL, and SOR entries are not populated.

This is both a governance gap and a documentation gap. For every selectable server, record:

- Owner and authentication method.
- Inspection date and next review date.
- Exact tools and schemas.
- Read/write capability.
- Maker and Checker access.
- Rate limits, pagination, error behavior, and safe test evidence.

Relevant reference: [MCP inspection inventory](mcp-inspection-inventory.md).

#### 8. Knowledge-base registry is not operationally complete

The registry contains placeholder or pending values for NICE, Omilia, CRM, and downstream API repositories. This prevents specialists from reliably following the documented “knowledge base first, MCP second” rule.

Each entry should have a verified organization, repository, branch, path, owner, access method, last validation date, and status. If a repository is unavailable, document the blocker and approved MCP/manual fallback instead of leaving a placeholder.

Relevant reference: [Knowledge-base registry](knowledge-base-registry.md).

### Medium Priority: Lifecycle Documentation

#### 9. Observability run-record construction

The exporter, schema, example, and skill exist, but the repository does not provide a complete implementation example showing how the Supervisor and each sub-agent append spans, how a run is closed, or how the Checker and approval outcomes map to span status.

Add a worked run-record example with:

- One complete trace.
- Span ownership by flow stage.
- Required and optional attributes.
- Redaction examples.
- Failure, blocked, and escalation events.
- Console, Logfire, and OTLP verification.

Relevant references:

- [Agent observability skill](../.github/skills/agent-observability/SKILL.md)
- [Observability README](../observability/README.md)
- [Run-record schema](../observability/schema/run-record.schema.json)
- [Example run record](../observability/examples/run-record.example.json)

**Recommended document:** `docs/observability-run-records.md`.

#### 10. Test-generation and CI integration

The test-script skill describes defect, development, and CRM-specific generation, but the repository does not show the complete path from generated test to the automation repository, pipeline, JUnit result, and report artifact.

Document:

- Generated test naming and location.
- Required test-data and environment variables.
- How a generated test is reviewed.
- Which pipeline runs it.
- How a failed test blocks promotion.
- Where JUnit and Playwright artifacts are published.

Relevant references:

- [Test-script generation skill](../.github/skills/test-script-generation/SKILL.md)
- [CRM gate pipeline](pipelines/azure-pipelines-crm-dev-gate.yml)
- [USL pipeline](pipelines/usl-2704-junit-fix/azure-pipelines.yml)
- [API evidence index](pipelines/usl-2704-junit-fix/api-evidence/INDEX.md)

**Recommended document:** `docs/test-generation-and-ci.md`.

#### 11. Pipeline catalogue and release gates

The pipeline YAML files are present, but there is no catalogue describing which pipelines are draft, manual, blocking, optional, or production-ready. The CRM pipeline explicitly contains a placeholder SIT deployment step, and the observability pipeline has no surrounding operator guide.

Add a table covering trigger, prerequisites, secrets/variable groups, gate behavior, artifacts, owners, and rollback for every pipeline.

**Recommended document:** `docs/pipelines.md`.

#### 12. Extension and change-management guide

There is no guide for adding a new domain agent, specialist, skill, MCP server, output contract field, or model policy. The repository should document naming, YAML frontmatter, required sections, test expectations, MCP inspection, review ownership, and rollout/rollback.

**Recommended document:** `docs/extending.md`.

#### 13. Procedure-learning promotion workflow

`PROCEDURE-LEARNING.md` exists and the agents require learning injection status, but there is no contributor-facing workflow for proposing, reviewing, approving, rejecting, or retrieving procedure lessons.

Document the entry format, evidence threshold, human review, stale-lesson handling, and how future agents discover applicable lessons.

Relevant references:

- [Procedure learning file](../.github/skills/fix-recommendation/PROCEDURE-LEARNING.md)
- [Fix recommendation skill](../.github/skills/fix-recommendation/SKILL.md)
- [Reliability and learning design](agent-reliability-learning-design.md)

## Existing Documentation That Should Be Linked from the Entry Point

The repository has useful material, but it is spread across several locations. The root README should provide a short navigation table linking to:

- Architecture and end-to-end flow.
- Setup and agent execution.
- Native versus Python deployment modes.
- MCP configuration, inspection, and knowledge-base registry.
- Security, governance, and human approval.
- Testing and pipeline operation.
- Observability and troubleshooting.

Current entry points:

- [README1.md](../README1.md)
- [Global Copilot instructions](../copilot-instructions.md)
- [End-to-end flow](end-to-end-flow.md)
- [Enterprise architecture](enterprise-agent-architecture.md)
- [AI governance](ai-governance.md)
- [Python Function README](../agents/python/skill-agent-function/README.md)
- [Observability README](../observability/README.md)

## Suggested Backlog

| Priority | Documentation task | Depends on |
| --- | --- | --- |
| P0 | Add `docs/setup.md` | None |
| P0 | Add `docs/running-agents.md` | Setup decisions |
| P0 | Add deployment-mode comparison | Confirm supported runtime modes |
| P0 | Add `docs/deployment.md` and `docs/security.md` | Environment and security owners |
| P1 | Complete MCP inspection inventory | MCP Inspector access and owners |
| P1 | Complete knowledge-base registry | Repository access verification |
| P1 | Add `docs/troubleshooting.md` | Setup and deployment decisions |
| P1 | Add observability run-record walkthrough | Confirm runtime emission ownership |
| P1 | Add test-generation and CI integration guide | Automation repository owners |
| P2 | Add pipeline catalogue | Pipeline owners |
| P2 | Add extension guide | Review and release conventions |
| P2 | Document procedure-learning promotion | Human review owner |
| P2 | Ratify retention and compliance policy | Data/privacy owner |

## Audit Conclusion

The repository is well documented at the architecture and policy level, but not yet documented as an operational product. The next documentation increment should focus on setup, invocation, deployment modes, security, and troubleshooting. The pending MCP and knowledge-base records should be treated as readiness blockers, not merely editorial cleanup, because agents are instructed to rely on those records when selecting evidence sources.
