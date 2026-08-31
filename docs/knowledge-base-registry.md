# Knowledge Base Registry

## Purpose

This registry defines the GitHub-hosted code repositories used as a **local knowledge base** by domain and specialist agents before they call an MCP. Agents must consult this registry first. An MCP call is a fallback, not the first step.

This design addresses the leadership decision from 19 Aug 2026: agents searching repositories blindly through MCP were consuming excessive tokens (especially for NICE and Omilia script discovery). Hosting the relevant codebase in a GitHub repository and pointing agents to it allows local resolution without MCP round-trips.

## Lookup Rule (applies to all agents)

```
1. Check this registry for a matching domain and component.
2. If an entry exists → clone or reference the listed GitHub repository branch locally.
3. Search the local clone for the relevant file, script, or class.
4. Only call the MCP if the local clone does not contain the required evidence.
5. Document which source (local KB or MCP) was used in the evidence summary.
```

## Knowledge Base Entries

| Domain | Component / System | GitHub Organisation | Repository | Branch | Index scope | Owner | Last verified |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CCaaS — NICE | NICE routing scripts and IVR flows | `<org>` | `<nice-scripts-repo>` | `main` | `/scripts/`, `/flows/` | Paramjeet Bungai | Pending — to be populated after Sandip review |
| CCaaS — Omilia | Omilia dialogue, intent, and NLU definitions | `<org>` | `<omilia-repo>` | `main` | `/dialogues/`, `/intents/` | Paramjeet Bungai | Pending — Omilia PAT bypass issue must be resolved first (see MCP Inspection Inventory) |
| CRM | D365 plugins, custom entities, Power Automate flows | `<org>` | `<crm-repo>` | `R3CodeReview_Kumar_2026.08.05` | `/plugins/`, `/flows/` | Suvendu Kumar Pattnaik | See also `docs/repository-registry.md` |
| CRM — Test Automation | Playwright + TypeScript CRM test framework (test scripts, page objects, API clients) | `greenshieldcanada` | `automation-scripts` (project `GSH-CRM`) | `enh-automation` | `tests/`, `lib/api/`, `pages/`, `fixtures/`, `data/` | Suvendu Kumar Pattnaik | Authoritative source for CRM test generation and the Dev→SIT quality gate. In-repo test-generation multi-agent under `.github/agents/`. |
| Downstream API | USL and SOR service contracts and handlers | `<org>` | `<api-repo>` | `main` | `/src/`, `/handlers/` | TBD | Pending |

> **To add an entry:** fill in the organisation, repository, branch, and index scope. Verify access using the PAT or service account for the relevant agent. Do not hard-code tokens in agent definitions — agents must prompt for credentials or use the configured MCP auth profile.

## Token Reduction Strategy

The following agents were identified as highest token consumers in the 19 Aug 2026 review. Priority is to populate their knowledge-base entries first:

1. **NICE Agent** — searching for IVR/routing scripts via MCP without a local reference
2. **Omilia Agent** — searching for dialogue/intent definitions via MCP without a local reference

Until these entries are populated and verified, the interim fix agreed on 19 Aug 2026 applies:
- Remove MCP code-extraction steps from the NICE and Omilia agent prompts.
- Manually supply the relevant script or file content to the agent context for the task.

## GitHub Copilot RAG Integration

Once the repositories above are confirmed and accessible:

1. Add the repository as a GitHub Copilot workspace or indexable source (settings → Copilot → repositories).
2. Agents reference the knowledge-base entry in this registry and Copilot resolves the file locally before calling any MCP.
3. Update the `Last verified` date after each repository restructure or branch change.

## Access and Credentials

- Use a dedicated **read-only service account or PAT user** for each knowledge-base repository.
- Do not reuse personal PAT tokens that have write access to production environments.
- Follow the same least-privilege rule as the MCP Inspection Inventory.
- For NICE: use the dedicated read-only PAT user created under Paramjeet's email (see MCP Inspection Inventory).
- For Omilia: pending resolution of the PAT scope bypass issue. Do not grant write-capable tokens.
