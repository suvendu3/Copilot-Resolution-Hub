# Agent Observability

Turns the multi-agent defect workflow into **queryable distributed traces** using
**OpenTelemetry** and **Logfire**. This is a post-hoc telemetry exporter, not
orchestration — it reads a structured *run-record* and ships spans to a backend.

- Governance / contract: [.github/skills/agent-observability/SKILL.md](../.github/skills/agent-observability/SKILL.md)
- Run-record schema: [schema/run-record.schema.json](schema/run-record.schema.json)
- Example run-record: [examples/run-record.example.json](examples/run-record.example.json)
- Exporter: [emit_traces.py](emit_traces.py)

## Why Logfire (not LangSmith)
The agents run inside GitHub Copilot agent mode, not a LangChain/LangGraph Python
runtime, so LangSmith auto-instrumentation does not apply. **Logfire is
OpenTelemetry-native**, accepts plain spans, and exports over standard OTLP — so
the same run-records can also target Grafana Tempo, Jaeger, Honeycomb, or Azure
Monitor by changing only the endpoint.

## Model
- **One trace per defect / work item.** Root span carries `work_item_id` and `system`.
- **One span per step:** supervisor enrich, input guardrail, routing, MCP evidence
  calls (nested), Maker propose, Checker verdict, model escalation, output guardrail,
  approval gate.
- **Events** capture point-in-time facts: guardrail blocks, Checker rejections,
  escalation triggers, human-approval requests.

## Setup
```powershell
# From repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r observability/requirements.txt
```

## Run
```powershell
# 1) Console mode — no account, great for demos and CI smoke checks
python observability/emit_traces.py --input observability/examples/run-record.example.json --console

# 2) Logfire (default) — set a write token first
$env:LOGFIRE_TOKEN = "<your-logfire-write-token>"
python observability/emit_traces.py --input observability/examples/run-record.example.json

# 3) Any OTLP backend (Tempo / Jaeger / Honeycomb / Azure Monitor)
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
python observability/emit_traces.py --input observability/examples/run-record.example.json --otlp
```

## Flags
| Flag | Effect |
| --- | --- |
| `--input <path>` | Run-record JSON to emit (required). |
| `--console` | Print spans locally; no backend/account needed. |
| `--otlp` | Export via OTLP/HTTP using `OTEL_EXPORTER_OTLP_ENDPOINT`. |
| `--service <name>` | Sets `service.name` (default `copilot-resolution-hub`). |
| `--fail-on-secret` | Exit non-zero if a secret-like attribute value is detected. |
| *(default)* | Logfire, using `LOGFIRE_TOKEN`; falls back to console if not installed. |

## Redaction
Telemetry is bound by [io-guardrails](../.github/skills/io-guardrails/SKILL.md).
Never put secrets, PATs, connection strings, auth headers, or PII into span names,
attributes, or events. The exporter runs a light secret scan and warns (or fails
with `--fail-on-secret`), but redaction must happen upstream when the run-record is
built.

## How agents produce run-records
Each agent appends its own span object to the run-record as the run progresses; the
Supervisor owns creation and final emission. See the run-record contract in the
[skill](../.github/skills/agent-observability/SKILL.md#run-record-contract).
