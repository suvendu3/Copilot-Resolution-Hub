---
name: mcp-governance
description: Use when selecting, inspecting, and governing MCP usage for defect investigation and evidence gathering, including MCP Inspector pre-approval checks.
---

# MCP Governance Skill

## Purpose
Define consistent MCP selection and usage rules for enterprise defect analysis.

## Rules
- Use only the MCP that owns the evidence.
- Prefer read-only investigation.
- Avoid duplicate MCP calls for the same evidence unless the first call was incomplete.
- Keep specialized evidence inside the specialist agent whenever possible.
- Do not add an MCP to an agent prompt until its server and intended tools are recorded in [docs/mcp-inspection-inventory.md](../../../docs/mcp-inspection-inventory.md).

## MCP Inspector Workflow

Use MCP Inspector when onboarding an MCP server, after a server/version/authentication change, after a material tool-schema change, or when a Maker or Checker cannot reproduce expected evidence retrieval.

1. Read the candidate server configuration from `.vscode/mcp.json`; do not copy tokens, connection strings, or production payloads into the inspection record.
2. Launch the Inspector from the repository root with `npx @modelcontextprotocol/inspector` and connect using the configured transport:
	- `stdio`: use the configured command and arguments.
	- `http`: use the configured server URL and the approved authentication flow.
3. Record the server identity, transport, owner, authentication method, tool/resource/prompt inventory, and version or inspection date in [docs/mcp-inspection-inventory.md](../../../docs/mcp-inspection-inventory.md).
4. Inspect input schemas and call only safe read-only tools with non-sensitive test data. Confirm response shape, authorization behavior, errors, pagination, and rate limits where applicable.
5. Classify each tool as `Maker`, `Checker`, `Both`, or `Not approved`. A tool is eligible for `Checker` only when the Checker can independently obtain the relevant evidence.
6. Record the result as `approved`, `restricted`, `blocked`, or `retired`. Escalate any write-capable tool, excessive data exposure, missing authorization boundary, or unredacted secret to a human owner.

## Approval Gates

- **Approved:** Server connects with the intended identity; expected schemas and safe read-only evidence retrieval work; owner and review date are recorded.
- **Restricted:** The MCP is usable only by a named specialist, environment, or agent role. Document the restriction explicitly.
- **Blocked:** Authentication, schema, least-privilege, ownership, or independent Checker evidence retrieval is unresolved. Do not reference it in a production agent workflow.
- **Retired:** The server or tool must not be selected; retain only the non-sensitive historical record.

## Maker and Checker Access Rules

- The Maker may use approved tools to gather proposal evidence.
- The Checker may use only tools marked `Checker` or `Both`; it must not rely solely on Maker-provided output when independent access is expected.
- Use Inspector results to define allowed tools, not to replace task-specific evidence collection or validation.
- Inspector is an administrative/development client. It is not an MCP server and is not invoked during every defect or development task.

## Evidence Handling

- Store only metadata, tool names, schema summaries, non-sensitive test identifiers, and outcome statuses in the inventory.
- Never store credentials, access tokens, authorization headers, customer records, raw production responses, or screenshots containing sensitive data.
- Link to approved internal evidence only when access-controlled and permitted by the data owner.

## Notes
- D365 MCP owns CRM metadata and Dataverse evidence.
- Azure MCPs own function app and Azure resource evidence.
- NICE MCP owns routing and IVR evidence.
- Omilia MCP owns intent and dialogue evidence.

## MCP Access Guardrails (added 19 Aug 2026)

These rules were adopted after the leadership review identified that the Omilia MCP was bypassing PAT token scope and accessing all environment groups regardless of the token's intended restriction.

### PAT Token Scope Rules
- Always use a **dedicated read-only service account or PAT user** for each MCP. Never use a personal developer PAT that has write access to any environment.
- A PAT token granted for one environment group (e.g., admin) must not be assumed to restrict access to other groups. Omilia's MCP was observed surpassing PAT scope and accessing UAT/SIT/Dev groups regardless of the token provided. Do not rely on PAT scope alone as a guardrail for Omilia.
- For NICE: use the dedicated read-only PAT user (created under Paramjeet Bungai's account) with restricted access only. Do not enable write-capable permissions on this user.
- For Omilia: **do not use the MCP to extract code or scripts** until the PAT scope bypass issue is resolved. Supply code to the agent context manually or via the local knowledge base (see `docs/knowledge-base-registry.md`).

### Code Extraction Guardrail
- Agents must **not** use MCP calls to extract source code files or scripts speculatively. Speculative code extraction is the primary cause of token overconsumption.
- Before calling an MCP for code, check `docs/knowledge-base-registry.md` for a local repository entry.
- If the local knowledge base contains the file, use it. Only call the MCP if the local source is missing or incomplete.
- Remove any MCP tool calls that pull entire codebases, directory trees, or unscoped file lists.

### Context Budget (added 26 Aug 2026)
- Treat the context window as the scarce resource. Gather the **smallest evidence set that can explain or falsify the hypothesis**, not the largest available.
- Prefer targeted reads (specific record, script, log range, or file section) over full documents or directory listings.
- When evidence exceeds what a handoff needs, **summarize to the decision-relevant facts** before passing it between agents; link to the source rather than inlining large payloads.
- Default guidance: keep the evidence in a single Maker Handoff focused and reviewable. If evidence is large, cite locations (file, line, record ID) instead of pasting full content.

### Agent Instruction Bypass Risk
- Agents may receive instructions like "don't access environment X" but the underlying MCP or user's account permissions may override those instructions.
- Instruction-based guardrails in agent markdown are **not sufficient** for security or access control. They complement, but do not replace, infrastructure-level access restrictions.
- For write-capable operations or cross-environment risks, escalate to a human approver rather than relying on agent instruction compliance.

### Read-Only Enforcement
- All MCP tools used by NICE and Omilia agents must be classified as read-only in the MCP Inspection Inventory.
- Any tool capable of write, update, delete, or environment-switching must be classified `Not approved` until a human owner reviews and explicitly approves it.
