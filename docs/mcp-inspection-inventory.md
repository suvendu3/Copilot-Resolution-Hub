# MCP Inspection Inventory

## Purpose

This inventory records the MCP servers and tools approved for agent evidence gathering after an MCP Inspector review. It is an operational governance record, not a source of production data.

MCP Inspector is used during onboarding and change review to inspect an MCP server's tools, resources, prompts, input schemas, authentication behavior, and safe read-only responses. It is not part of the runtime Maker/Checker task path.

## Operating Procedure

1. Start from the shared server configuration in [`.vscode/mcp.json`](../.vscode/mcp.json).
2. From the repository root, run `npx @modelcontextprotocol/inspector`.
3. Connect with the configured transport and the approved authentication method.
4. Inspect and safely exercise only read-only tools using non-sensitive test inputs.
5. Update the server entry and each approved tool row below. A named owner reviews the entry after any server, tool-schema, authentication, or permission change.
6. Follow the complete approval and data-handling rules in the [MCP Governance Skill](../.github/skills/mcp-governance/SKILL.md).

## Status Definitions

| Status | Meaning |
| --- | --- |
| `pending` | Configured or planned, but not yet inspected. Agents must not rely on it for governed evidence. |
| `approved` | Inspection confirmed the expected least-privilege behavior and safe evidence retrieval. |
| `restricted` | Approved only for documented agents, environments, or use cases. |
| `blocked` | An authorization, ownership, safety, schema, or Checker-independence issue prevents use. |
| `retired` | No longer selectable by agents. |

## Server Inventory

| Server ID | Domain / owner | Transport | Authentication | Inspection status | Last inspected | Inspector / owner | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pac-mcp` | Power Platform / platform engineering | `stdio` | Local PAC authenticated profile | `pending` | Not inspected | Unassigned | Configured in `.vscode/mcp.json`; use for approved Power Platform evidence only after inspection. |
| `pac-mcp-pac-cli` | Power Platform / platform engineering | `stdio` | Local PAC CLI authenticated profile | `pending` | Not inspected | Unassigned | Fallback PAC configuration; inspect separately because the launch method differs. |
| `pac-mcp-dnx` | Power Platform / platform engineering | `stdio` | PAC CLI through `dnx` and local authenticated profile | `pending` | Not inspected | Unassigned | Fallback PAC configuration; confirm tool parity with the primary server. |
| `ado-remote-mcp` | Azure DevOps / DevOps platform owner | `http` | Approved Azure DevOps authentication flow | `pending` | Not inspected | Unassigned | Use for work-item, repository, and pipeline evidence after inspection. |
| `nice-mcp` | CCaaS — NICE / Paramjeet Bungai | `http` | Dedicated read-only PAT user (created under Paramjeet Bungai account; restricted access only) | `restricted` | 2026-08-19 | Paramjeet Bungai | Read-only PAT user confirmed. Do not enable write-capable permissions. Pass this PAT to Ardhendu's team for investigation tasks only. |
| `omilia-mcp` | CCaaS — Omilia (Amelia) / Paramjeet Bungai | `http` | PAT token (group-scoped) | `blocked` | 2026-08-19 | Paramjeet Bungai | **Critical:** Omilia MCP bypasses PAT scope — even a group-restricted PAT results in access to all groups (Admin, Dev, SIT, UAT). Raised with Amelia engineering; their engineer confirmed MCP was created but not internally used or tested. Do not use for code extraction until scope isolation is confirmed. Use local knowledge base (docs/knowledge-base-registry.md) as interim. Raise formal ticket to Amelia vendor. |
| `<future-server-id>` | `<domain / owner>` | `stdio` or `http` | `<approved method>` | `pending` | Not inspected | `<name>` | Add D365, Azure, USL, or SOR servers here before agent adoption. |

## Approved Tool Inventory

Add one row for each agent-eligible tool. Tool-level approval matters because an otherwise approved MCP can expose a tool that is write-capable or outside the intended domain.

| Server ID | Tool / resource / prompt | Capability | Agent access | Inspection result | Test evidence reference | Last reviewed | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<server-id>` | `<exact exposed name>` | Read-only evidence / write / resource / prompt | `Maker`, `Checker`, `Both`, or `Not approved` | `approved`, `restricted`, `blocked`, or `retired` | `<non-sensitive test ID or approved link>` | `<YYYY-MM-DD>` | `<schema, pagination, restrictions, or failure behavior>` |

## Review Checklist

- [ ] Server identity and owner are known.
- [ ] Transport and approved authentication method work without exposing secrets.
- [ ] Intended tool names and input schemas match the agent workflow.
- [ ] Read-only evidence retrieval was tested with non-sensitive inputs.
- [ ] Write-capable or high-risk tools are marked `Not approved` unless a separate human approval exists.
- [ ] The Checker can independently access the required evidence, or the limitation is marked `blocked` or `restricted`.
- [ ] Response handling, pagination, rate limits, and error behavior are documented where relevant.
- [ ] The inspection date and next review owner are recorded.