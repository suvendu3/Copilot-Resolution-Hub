# AI Governance — Copilot Resolution Hub

> Consolidated AI governance policy for the native GitHub Copilot multi-agent defect-resolution
> system. This document maps the controls that already exist across agents, skills, and docs to the
> **NIST AI Risk Management Framework (AI RMF 1.0)** functions — **Govern, Map, Measure, Manage** —
> and defines ownership, review cadence, data/model policies, and tracked gaps.
>
> Scope: the agents in `.github/agents/`, skills in `.github/skills/`, MCP evidence tools, the
> observability exporter in `observability/`, and the operating rules in
> [copilot-instructions.md](../copilot-instructions.md).

## 1. Governance Principles
- **Human accountability is final.** AI produces recommendations, not autonomous production changes.
  High-risk, production, security, data-integrity, and cross-system actions require human approval.
- **Separation of duties.** The Maker proposes and cannot self-certify; the Checker validates and
  cannot silently rewrite. No single agent both proposes and approves.
- **Evidence-grounded, not generative-by-default.** Every root cause, file, and fix must trace to an
  Evidence Bundle sourced from an approved MCP or local knowledge base.
- **Least privilege for tools and data.** Read-only service accounts/PATs; MCP tools are approved and
  periodically re-inspected before use as evidence.
- **Defense in depth.** Markdown guardrails are advisory; enforcement relies on infrastructure
  controls (read-only PATs, DLP, access scoping, the Human Approval Gate).
- **Traceability.** Every defect run is observable end to end as a distributed trace.

## 2. Control Map (NIST AI RMF)

### 2.1 GOVERN — policies, roles, accountability
| Control | Implementation | Evidence artifact |
| --- | --- | --- |
| Operating modes & success criteria | [copilot-instructions.md](../copilot-instructions.md) | Defect vs Development mode rules |
| Separation of duties | [maker-agent](../.github/agents/maker-agent.md), [checker-agent](../.github/agents/checker-agent.md) | Versioned Maker handoff + Checker verdict |
| Human-in-the-loop | [human-approval](../.github/skills/human-approval/SKILL.md) | Approval gate decisions |
| Tool governance | [mcp-governance](../.github/skills/mcp-governance/SKILL.md), [mcp-inspection-inventory.md](mcp-inspection-inventory.md) | Inspection/approval records |
| This policy | `docs/ai-governance.md` | Reviewed per cadence in §5 |

### 2.2 MAP — context, scope, and risk framing
| Control | Implementation |
| --- | --- |
| Pre-LLM scope filter (deterministic, no model call) | [io-guardrails](../.github/skills/io-guardrails/SKILL.md) Layer 0 |
| Scope allow-list / off-topic reject | io-guardrails Input Guardrail 2 |
| Input completeness for stories/CRs | [user-story-validation](../.github/skills/user-story-validation/SKILL.md) |
| System routing to correct domain | [system-routing](../.github/skills/system-routing/SKILL.md), [enterprise-defect-triage](../.github/skills/enterprise-defect-triage/SKILL.md) |

### 2.3 MEASURE — assessment, metrics, testing
| Control | Implementation | Primary signal |
| --- | --- | --- |
| Evidence grounding & relevancy checks | io-guardrails Output Guardrails | Ungrounded/irrelevant → flag-and-escalate |
| Independent validation | [checker-agent](../.github/agents/checker-agent.md) | `validated` / `rejected` / `blocked` / `needs_human_approval` |
| Reliability & learning metrics | [agent-reliability-learning-design.md](agent-reliability-learning-design.md) | Append-only eval records |
| Run telemetry | [agent-observability](../.github/skills/agent-observability/SKILL.md), [observability/](../observability/README.md) | Trace per run; guardrail-block, rejection, escalation rates |
| CI smoke gate | [azure-pipelines-observability-smoke.yml](pipelines/azure-pipelines-observability-smoke.yml) | Exporter + secret-leak check |

### 2.4 MANAGE — response, mitigation, and recovery
| Control | Implementation |
| --- | --- |
| Input security block | io-guardrails HARD-BLOCK (injection, secret/PII, out-of-scope, unapproved writes) |
| Output security block | io-guardrails secret/sensitive-data scan before delivery |
| Write/risk gate to human | io-guardrails Write-action gate + [human-approval](../.github/skills/human-approval/SKILL.md) |
| Model escalation on low confidence | [copilot-instructions.md — Model Selection Policy](../copilot-instructions.md) |
| Post-fix learning capture | `.github/skills/fix-recommendation/PROCEDURE-LEARNING.md` |
| Rollback rules | [agent-reliability-learning-design.md](agent-reliability-learning-design.md) |

## 3. Data Governance (evidence & telemetry)
- **Redaction before use.** Secrets, PATs, connection strings, authorization headers, and customer
  PII must be stripped before entering agent context and before any telemetry span is emitted
  (see [io-guardrails](../.github/skills/io-guardrails/SKILL.md) and
  [agent-observability](../.github/skills/agent-observability/SKILL.md)).
- **Telemetry minimization.** Observability spans carry only low-cardinality identifiers, enums, and
  counts — never raw payloads, log bodies, or customer records. The exporter runs a secret scan and
  can fail closed (`--fail-on-secret`).
- **Retention (to be ratified by owner).** Recommended defaults: agent traces retained 90 days in the
  observability backend; evaluation records retained per the reliability-learning design; no customer
  data persisted in traces or eval records. Confirm against enterprise data-retention and residency
  policy before production use.
- **Secrets handling.** No secrets in the repo; MCP credentials use `${input:...}` prompts in
  [.vscode/mcp.json](../.vscode/mcp.json). `.gitignore` excludes env files and local sensitive content.

## 4. Model Governance
- **Approved model tiers.** Complexity-based selection with a documented escalation path to a
  higher-capability model for high-risk/low-confidence tasks
  ([copilot-instructions.md — Model Selection Policy](../copilot-instructions.md)).
- **Escalation triggers (auditable).** Two consecutive Checker rejections, unresolved root-cause
  ambiguity after authoritative evidence, or production/security/data-integrity impact with low
  confidence.
- **Change control.** Changes to allowed models or escalation thresholds are made by editing the
  policy file via reviewed pull request; the model used per run is recorded on the observability
  `maker.*` / `checker.*` spans for audit.

## 5. Roles & Review Cadence (RACI)
> Replace role placeholders with named owners before ratification.

| Activity | Responsible | Accountable | Consulted | Informed | Cadence |
| --- | --- | --- | --- | --- | --- |
| Guardrail rules (io-guardrails) | Platform lead | Eng manager | Security | Team | Quarterly + on incident |
| MCP tool approval / re-inspection | MCP owner | Eng manager | Security | Team | Per new tool + quarterly |
| Model policy & escalation thresholds | AI lead | Eng manager | Data/Privacy | Team | Quarterly |
| Telemetry retention & redaction | Data owner | Privacy officer | Platform lead | Team | Semi-annual |
| Human approval gate outcomes | Approver on duty | Eng manager | — | Requester | Per request |
| This governance doc | Platform lead | Eng manager | Security, Privacy | Team | Quarterly |

## 6. Human Approval Gate — mandatory triggers
Route to [human-approval](../.github/skills/human-approval/SKILL.md) before delivery when any is true:
- Production, security, or data-integrity impact.
- Any write/destructive action recommendation.
- Cross-system dependency with unresolved evidence conflicts.
- Checker verdict `needs_human_approval`, or two consecutive `rejected` verdicts.

## 7. Incident Response (AI-specific)
1. **Detect** — a bad recommendation, guardrail bypass, or secret/PII leak is identified (often via a
   `status=blocked`/`error` span or a failed CI secret scan).
2. **Contain** — halt the affected workflow; do not action the recommendation; revoke/rotate any
   exposed credential.
3. **Trace** — pull the run trace (`run_id`) to reconstruct every agent hop, guardrail verdict, and
   MCP call.
4. **Correct** — patch the guardrail/skill/policy via reviewed PR; add a regression check.
5. **Learn** — record the lesson in `.github/skills/fix-recommendation/PROCEDURE-LEARNING.md` and,
   if systemic, update this policy.

## 8. Open Gaps (tracked)
| # | Gap | Recommended action | Owner |
| --- | --- | --- | --- |
| G1 | Retention/residency for telemetry not ratified | Confirm against enterprise data policy; set backend retention | Data owner |
| G2 | Guardrail/injection rules are advisory-only | Add automated regression tests proving key blocks hold | Platform lead |
| G3 | No tracked hallucination/grounding-failure rate trend | Build dashboards from observability spans | AI lead |
| G4 | No token/cost budget policy | Define per-run budget + alerting | Eng manager |
| G5 | Model change-control not formally signed off | Add approval step to model-policy PRs | AI lead |
| G6 | RACI role placeholders unfilled | Assign named owners and ratify | Eng manager |

## 9. References
- NIST AI RMF 1.0 (Govern / Map / Measure / Manage).
- ISO/IEC 42001 (AI management system) and EU AI Act risk tiers — for future alignment.
- Internal: [enterprise-agent-architecture.md](enterprise-agent-architecture.md),
  [agent-reliability-learning-design.md](agent-reliability-learning-design.md),
  [mcp-inspection-inventory.md](mcp-inspection-inventory.md).
