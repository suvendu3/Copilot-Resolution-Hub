---
name: agent-observability
description: Use to make the multi-agent defect workflow observable. Defines a structured run-record each agent emits (trace per defect, span per agent hop / guardrail / model escalation / MCP call) and maps it to OpenTelemetry so it can be shipped to Logfire or any OTLP backend. Covers what to capture, what to redact, and how to run the emitter.
---

# Agent Observability Skill

## Purpose
Give the markdown-driven agent workflow real, queryable telemetry without adding orchestration code. Each agent already produces a Guardrail Result Record and an Output Format; this skill standardizes a single **run-record** that captures the full defect run as a distributed trace:

- **One trace per defect / work item** (`trace_id` = ADO work item id or a generated run id).
- **One span per meaningful step**: Supervisor enrich, input guardrail, triage, routing decision, each domain/sub agent hop, each MCP evidence call, Maker proposal, Checker verdict, model escalation, output guardrail, human-approval gate.

The run-record is plain data. A separate exporter ([observability/emit_traces.py](../../../observability/emit_traces.py)) converts it to OpenTelemetry spans and ships them to **Logfire** (OTel-native) or any OTLP endpoint. Nothing here participates in routing decisions — it is post-hoc telemetry only, consistent with the repository's no-orchestration-code rule.

## Why Logfire + OpenTelemetry (not LangSmith)
- The agents run inside GitHub Copilot agent mode, not a LangChain/LangGraph Python runtime, so **LangSmith** auto-instrumentation does not apply.
- **Logfire** is OpenTelemetry-native, accepts plain spans (no framework lock-in), and exports over standard **OTLP** — so the same run-records can also flow to Grafana Tempo, Jaeger, Honeycomb, or Azure Monitor by changing only the endpoint, never the emission format.

## When to Use
- The Supervisor or any agent finishes a step and needs to append its span to the current run-record.
- A run completes and you want to ship the trace to Logfire for inspection, dashboards, or SLO tracking.
- You are debugging routing drift, guardrail blocks, repeated Checker rejections, or model-escalation frequency.

## Run-Record Contract
Emit a JSON object that conforms to [observability/schema/run-record.schema.json](../../../observability/schema/run-record.schema.json). Minimum shape:

```json
{
  "run_id": "AB#877491",
  "work_item_id": "877491",
  "system": "CRM",
  "started_at": "2026-08-31T09:00:00Z",
  "spans": [
    {
      "name": "supervisor.enrich",
      "agent": "supervisor-agent",
      "stage": "input",
      "started_at": "2026-08-31T09:00:00Z",
      "ended_at": "2026-08-31T09:00:02Z",
      "attributes": { "mcp": "ado", "decision": "routed" },
      "status": "ok"
    }
  ]
}
```

### Required span attributes (use only what applies)
- `agent` — emitting agent name (matches `.github/agents/*`).
- `stage` — `input` | `route` | `evidence` | `propose` | `check` | `output` | `approval`.
- `decision` / `verdict` — routing target, `approved`/`rejected`, guardrail `pass`/`blocked`.
- `guardrail_check` — the specific check id when `stage` is `input`/`output`.
- `model` and `complexity` — record on Maker/Checker spans to observe escalation.
- `mcp` — MCP tool name on evidence spans.
- `evidence_count` — number of cited evidence items on proposal/verdict spans.
- `status` — `ok` | `blocked` | `error`.

### Events (point-in-time facts inside a span)
Record events for: guardrail hard-block, model escalation trigger, Checker rejection, human-approval request. Each event: `name`, `timestamp`, optional `attributes`.

## Redaction Rules (mandatory before emit)
Telemetry is not exempt from [io-guardrails](../io-guardrails/SKILL.md). Before writing any span:
- Never place secrets, PATs, connection strings, authorization headers, or customer PII in span names, attributes, or events.
- Store citations as identifiers or repo-relative paths, not raw payloads.
- Keep attribute values scalar and low-cardinality where possible (ids, enums, counts) — not full log bodies.

## How to Emit
1. Build/append the run-record JSON as the run progresses (agents append their own span objects).
2. Ship it:
   ```powershell
   # From repo root. Console mode needs no account (good for demos):
   python observability/emit_traces.py --input observability/examples/run-record.example.json --console

   # Send to Logfire (set token first):
   $env:LOGFIRE_TOKEN = "<your-logfire-write-token>"
   python observability/emit_traces.py --input path/to/run-record.json --service copilot-resolution-hub

   # Or any OTLP backend (Tempo/Jaeger/Honeycomb/Azure Monitor):
   $env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
   python observability/emit_traces.py --input path/to/run-record.json --otlp
   ```
3. The exporter creates a root span for the defect and nested child spans in order, preserving parent/child links and durations.

## What Good Looks Like
- Every routed defect produces exactly one trace whose root span carries `work_item_id` and `system`.
- Guardrail blocks and human-approval gates appear as spans with `status=blocked` and a matching event.
- Model escalations are visible as an event plus a `model`/`complexity` attribute change between Maker attempts.
- No secret or PII value appears anywhere in the exported trace.

## Related
- [io-guardrails](../io-guardrails/SKILL.md) — the Guardrail Result Record feeds the `input`/`output` spans.
- [mcp-governance](../mcp-governance/SKILL.md) — MCP evidence spans should reflect inspection status.
- [supervisor-agent](../../agents/supervisor-agent.md) — owns run-record creation and final emission.
