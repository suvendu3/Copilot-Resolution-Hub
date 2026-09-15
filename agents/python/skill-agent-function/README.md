# Skill Agent Function (standalone add-on)

Independent Azure Function that executes `.github/skills/*/SKILL.md` procedures
via an LLM call. This is **not** part of the native GitHub Copilot multi-agent
architecture described in [copilot-instructions.md](../../../copilot-instructions.md)
(that architecture stays markdown-only, no Python orchestration). This service
exists for automated / unattended contexts (CI/CD, scheduled jobs, external
callers) that need to invoke a skill outside the VS Code Copilot chat session.

## How it works
1. `skill_loader.py` reads a `SKILL.md` file (YAML frontmatter + markdown body).
2. `agent.py` wraps the skill body in a system prompt and sends the caller's
   input to Azure OpenAI via `llm_client.py`.
3. `function_app.py` exposes this over HTTP.
4. `graph.py` chains multiple skills into a single LangGraph `StateGraph` for
   graph-based agentic flows (see below), instead of one-shot single-skill calls.

## Graph-based agentic flow (LangGraph)
`graph.py` implements a `StateGraph` that chains skills into one flow:

```
pre_input_hook --(blocked)--> END
       |
   (continue)
       v
nemo_input_check --(blocked)--> END
       |
   (continue)
       v
input_guardrails --(blocked)--> END
       |
   (continue)
       v
    triage --> fix_recommendation --> pre_output_hook --(blocked)--> END
                                              |
                                          (continue)
                                              v
                                      nemo_output_check --(blocked)--> END
                                              |
                                          (continue)
                                              v
                                      output_guardrails --> END
```

Three layers of defense-in-depth guard both the input and the output, each
cheaper/faster layer running before the next:

- **pre_input_hook / pre_output_hook** — `guardrail_hooks.py`, deterministic
  regex (Layer 0 scope filter, secret/PII scan). Zero LLM cost.
- **nemo_input_check / nemo_output_check** — `nemo_rails.py`, NVIDIA NeMo
  Guardrails (Colang + `guardrails_config/`). See below.
- **input_guardrails / output_guardrails** — the `io-guardrails` **skill**
  itself, executed as an LLM call via `SkillAgent` (the richest, most
  context-aware check, and the one directly tied to the documented skill).
- **triage** — runs `enterprise-defect-triage` to classify the target system
  and route.
- **fix_recommendation** — runs `fix-recommendation`, given the triage result
  as additional context, to produce the evidence-backed fix.

Each LLM node is one `SkillAgent` call; `SkillAgent` instances are cached per
skill name in `graph.py` so the graph doesn't reparse `SKILL.md` on every
node. This graph is intentionally linear/small — extend it by adding more
nodes (e.g. `system-routing`, `human-approval`) and wiring conditional edges
off the parsed skill output, following the same pattern.

Call it via `POST /api/execute-graph` (see API section below).

## NeMo Guardrails (Colang + config.yml)
`guardrails_config/` holds the NVIDIA NeMo Guardrails configuration:
- `config.yml` — declares the main model (`engine: azure`) and which rails run
  on input (`scope allow list check`, `self check input`) and output
  (`self check output`).
- `prompts.yml` — the `self_check_input` / `self_check_output` prompt templates.
- `rails/general.co` — Colang flow wiring the deterministic
  `scope_allow_list_check` action (backed by `guardrail_hooks.pre_input_scope_filter`)
  into the input rails, plus the shared refusal message.

`nemo_rails.py` loads this config once (`get_rails()`), injects
`AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_VERSION` / `AZURE_OPENAI_DEPLOYMENT`
from environment variables at runtime (not hardcoded in `config.yml`), and
exposes `check_input(text)` / `check_output(text, original_input)` which run
only the input or only the output rails via `GenerationOptions(rails=[...])`.
Edit `guardrails_config/config.yml`'s `model:` placeholder only if you are not
setting `AZURE_OPENAI_DEPLOYMENT`.

## Local development
Dependencies (including `langchain` / `langgraph`, used for future multi-step
skill graphs) are installed with [`uv`](https://docs.astral.sh/uv/), not pip.

```powershell
cd agents/python/skill-agent-function
uv pip install -r requirements.txt --python ..\..\..\.venv\Scripts\python.exe
Copy-Item local.settings.json.example local.settings.json
# edit local.settings.json with your Azure OpenAI endpoint/key/deployment
..\..\..\.venv\Scripts\python.exe -m pytest tests/ -q
func start
```

Call it:
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:7071/api/execute-skill `
  -ContentType "application/json" `
  -Body (@{ skill = "enterprise-defect-triage"; input = "Bug 12345: D365 plugin throws null ref on contact update" } | ConvertTo-Json)
```

## Deployment (Azure Function)
1. Bundle skill files so the deployed package is self-contained:
   ```powershell
   python scripts/sync_skills.py
   ```
2. Provision a Function App (Consumption or Flex Consumption, Python 3.11) and
   an Azure OpenAI resource, then publish:
   ```powershell
   func azure functionapp publish <function-app-name>
   ```
3. Configure app settings (use Key Vault references for secrets, not plain values):
   ```powershell
   az functionapp config appsettings set --name <function-app-name> --resource-group <rg> --settings `
     AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/" `
     AZURE_OPENAI_DEPLOYMENT="<deployment-name>" `
     AZURE_OPENAI_API_VERSION="2024-08-01-preview"
   az functionapp config appsettings set --name <function-app-name> --resource-group <rg> `
     --settings AZURE_OPENAI_API_KEY="@Microsoft.KeyVault(SecretUri=<secret-uri>)"
   ```
4. `http_auth_level=FUNCTION` requires a function key on every call; rotate keys
   periodically and put the Function behind APIM/Front Door if exposed externally.

## Observability (Logfire)
`observability.py` configures [Logfire](https://logfire.pydantic.dev) (OpenTelemetry-native)
once at import, matching the model already used for the markdown agents in
[observability/README.md](../../../observability/README.md): one span per
graph node / skill call / HTTP request, never the full LLM prompt/response
(only skill name, decision, and a length-bounded preview).

- **`observability.traced_node(name)`** — wraps each LangGraph node
  (`pre_input_hook`, `nemo_input_check`, `input_guardrails`, `triage`,
  `fix_recommendation`, `pre_output_hook`, `nemo_output_check`,
  `output_guardrails`) in a `graph.<name>` span, logging `blocked` on completion.
- **`observability.traced_skill_call(name, preview)`** — wraps each
  `SkillAgent.run()` (one LLM call) in a `skill.<name>` span in `agent.py`.
- `function_app.py` wraps each HTTP route (`http.execute_skill`,
  `http.execute_graph`) in its own span so a request can be traced end-to-end.

Set `LOGFIRE_TOKEN` as a Function App setting (or in `local.settings.json`,
never committed) to ship spans to Logfire; without a token, spans print to
console only (`send_to_logfire="if-token-present"`), so this is safe to run
in tests/CI with no account. Optionally set `LOGFIRE_SERVICE_NAME` (defaults
to `skill-agent-function`).

## API
- `GET /api/health` — returns `{"status": "ok", "skills": [...]}`.
- `POST /api/execute-skill` — body: `{"skill": "<skill-name>", "input": "<text>", "context": {}}`.
  Returns `{"skill", "raw_output", "output"}` where `output` is parsed JSON when
  the model returned valid JSON, otherwise the raw text.
- `POST /api/execute-graph` — body: `{"input": "<text>", "context": {}}`.
  Runs the LangGraph flow (input guardrails -> triage -> fix recommendation ->
  output guardrails) and returns the full graph state, including
  `final_output` (`null` if blocked) and `error` when a guardrail blocked the flow.

## Security notes
- Skill names are validated against `^[a-z0-9][a-z0-9-]*$` and resolved paths
  are checked to stay inside the skills root (defense against path traversal).
- No secrets are read from source; only from Function App settings / Key Vault.
- Unhandled exceptions are logged server-side and return a generic 502 to the
  caller (no stack traces or internals are exposed).
- Re-run `scripts/sync_skills.py` whenever `.github/skills/*` changes so the
  deployed copy stays current.
- Logfire spans never include full skill input/output text - only a
  length-bounded preview and pass/blocked decisions (see Observability above).
