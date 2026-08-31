# Repository Registry

Use this registry to locate approved source repositories before a domain or specialist agent searches code. Update repository and branch information here rather than hard-coding it in agent definitions.

| Domain | System or component | Azure DevOps project | Repository | Branch | Repository link | Investigation notes |
| --- | --- | --- | --- | --- | --- | --- |
| CRM Contact Center | Azure Functions and CCaaS Azure components | `GSH-CRM` | `gs-ccas-azure-components` | `R3CodeReview_Kumar_2026.08.05` | [Open repository](https://dev.azure.com/greenshieldcanada/GSH-CRM/_git/gs-ccas-azure-components?version=GBR3CodeReview_Kumar_2026.08.05) | Use when Power Automate run history identifies an Azure Function action or dependency in the `GSH.Manual.SaveInteractionHistory` performance path. |
| CRM Test Automation | Playwright + TypeScript automation framework for D365 / Contact360 / Service360 | `GSH-CRM` | `automation-scripts` | `enh-automation` | [Open repository](https://dev.azure.com/greenshieldcanada/GSH-CRM/_git/automation-scripts?version=GBenh-automation) | Authoritative source for CRM test scripts and the automated Dev→SIT quality gate. Index scope: `tests/` (API + UI E2E specs named `TC-<ADO id>_*.spec.ts`), `lib/api/` (typed `USLApiClient`), `pages/` (page objects), `fixtures/`, `data/*.xlsx`. Reuse these conventions when generating new tests. Fast gate candidate: `tests/API` (+ `tests/Smoke`). An in-repo multi-agent test generator lives under `.github/agents/` and `AI_CONTEXT/`. Existing CI: `pipelines/Playwright_UI_Regression.yml` (qa/sit/uat, manual trigger, non-blocking). |

## Source Lookup Rules

1. **Check the knowledge base first.** Before searching ADO or calling an MCP for source code, check `docs/knowledge-base-registry.md`. If a matching entry exists for the domain and component, resolve the file from the listed GitHub repository branch locally.
2. Use the repository and branch in this registry when a work item identifies a matching component.
3. Search the supplied branch before default branches so the analysis matches the reported implementation.
4. Do not infer that a Power Automate flow calls an Azure Function solely because an Azure Functions repository exists. Confirm the dependency from flow run history, connection references, or a matching action/configuration.
5. If repository access fails, report the project, repository, branch, requested search terms, and the authentication error without exposing credentials.
