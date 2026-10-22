# AccessPilot: API

Defines how the frontend talks to the backend, how the backend talks to external services, and the rules every call follows. Source of truth: `PRD.md` and `architecture.md`. There is no `DATABASE.md`, because the product has no database. State is in memory, and its types are in `architecture.md` section 4.

Only the APIs the product needs are defined here. Do not add endpoints, error codes or integrations without updating this file and `architecture.md` in the same change.

---

## 1. Conventions

| Topic | Rule |
|-------|------|
| Base path | `/api` on the backend (default port 8000) |
| Versioning | None for the MVP. A breaking change updates the frontend and backend together. |
| Format | JSON request and response bodies, `Content-Type: application/json`, UTF-8 |
| Field names | camelCase |
| Times | ISO 8601 in UTC |
| IDs | Opaque strings. Clients never parse them. |
| Durations | Integer milliseconds in fields named `durationMs` |
| Unknown request fields | Rejected with `invalid_request` |
| Null versus missing | Optional fields are omitted when absent, except where the type allows `null` |
| Priority | Each endpoint is marked Tier 1, 2 or 3 as in `PRD.md` |

## 2. Authentication and authorization

### 2.1 Model

The MVP is a local, single-user tool. There are no accounts, sessions or passwords. Access is limited by where the server listens and by checks the server makes on every request.

| Control | Rule |
|---------|------|
| Network exposure | The backend binds to the loopback interface only by default (`BACKEND_HOST`). Binding to any other address needs a deliberate setting and is not supported for the demo. |
| Allowed browser origin | CORS allows only the configured frontend origin (`FRONTEND_ORIGIN`). No wildcard. |
| Secrets | Model credentials exist only in the backend's environment. They are never sent to the frontend, never returned by any endpoint, and never written to logs, traces or exports. |
| Frontend configuration | The frontend may hold only non-secret values (the API base URL). Nothing secret may use a `VITE_` prefix. |

If a hosted version is ever built, it needs real authentication, roles and per-user scan ownership. That is out of scope for now.

### 2.2 Authorization checks made on the server

The client is never trusted to enforce any of these.

| Check | Where | Failure |
|-------|-------|---------|
| Authorisation flag must be `true` on every scan request | `POST /api/scans` | `consent_required` |
| Target URL must pass the URL policy, including after redirects | `POST /api/scans` | `blocked_target` |
| Changes may only be applied when the scan's target is the bundled demo working copy | `POST /api/proposals/{id}/apply` | `apply_not_allowed` |
| A valid, unexpired, unused approval token that matches the current diff hash | `POST /api/proposals/{id}/apply` | `approval_required` |
| Every written file must resolve inside the working copy and be on the allowlist | Apply | `path_not_allowed` |
| Only the allowed parameters may be edited, with length limits | `PATCH /api/proposals/{id}` | `invalid_request` |
| The agent cannot call any endpoint. Its tools run inside the backend process and cannot approve, apply or set a status. | Agent service | Not exposed |

## 3. Endpoint overview

| Method | Path | Purpose | Tier |
|--------|------|---------|------|
| GET | `/api/health` | Backend status and whether a model is configured | 1 |
| POST | `/api/scans` | Scan a page and return findings | 1 |
| GET | `/api/scans/{id}` | Fetch a scan | 1 |
| POST | `/api/scans/{id}/agent` | Run the agent (or the built-in agent) | 1 |
| GET | `/api/scans/{id}/agent/stream` | Stream trace entries as they happen | 2 |
| GET | `/api/proposals/{id}` | Fetch a proposal with its diff | 1 |
| PATCH | `/api/proposals/{id}` | Edit allowed wording and regenerate the diff | 1 |
| POST | `/api/proposals/{id}/approve` | Issue a single-use approval token | 1 |
| POST | `/api/proposals/{id}/skip` | Mark a proposal skipped | 1 |
| POST | `/api/proposals/{id}/apply` | Apply to the working copy, re-test, return the result | 1 |
| POST | `/api/workspaces/{id}/rollback` | Restore the previous snapshot | 3 |
| GET | `/api/scans/{id}/export` | Download the JSON report | 2 |

## 4. Endpoint details

Response objects (`Scan`, `Finding`, `TraceEntry`, `Proposal`, `ApplyResult`, `AgentRun`) are defined in `architecture.md` section 4.

### 4.1 GET /api/health

Purpose: let the UI show whether the backend, the browser and a model are available.

Response 200 fields:

| Field | Type | Notes |
|-------|------|-------|
| `status` | string | `ok` when the API is running |
| `browserAvailable` | boolean | Whether Chromium can be launched |
| `modelConfigured` | boolean | True only if provider, base URL, key and model are all set |
| `modelName` | string or null | The configured model name. Never the key. |
| `engineVersion` | string | Version of the vendored rule engine |

### 4.2 POST /api/scans

Purpose: load a page in a real browser, run the rule engine, and return findings.

Request fields:

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `url` | string | Yes | Absolute `http` or `https` URL, at most 2048 characters |
| `consent` | boolean | Yes | Must be `true` |
| `keyboardWalk` | boolean | No (Tier 2) | Default `true` once the walk exists |

Response 201: a `Scan`. The response includes the trace. Scan duration is bounded by the scan timeout (section 12).

Errors: `invalid_request`, `consent_required`, `invalid_url`, `blocked_target`, `scan_failed`, `browser_unavailable`, `busy`.

A page that fails to load never returns an empty success. It returns `scan_failed`.

### 4.3 GET /api/scans/{id}

Purpose: fetch a stored scan. Response 200: a `Scan`. Errors: `not_found`.

### 4.4 POST /api/scans/{id}/agent

Purpose: produce plain-language explanations and proposals for the scan's findings.

Request fields (body optional):

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `mode` | string | No | `auto` (default) uses the model if configured, otherwise the built-in agent. `builtin` forces the built-in agent. |

Response 200: an `AgentRun`. `aiUsed` says whether a model was used. If it was not, or if it stopped early, `fallbackReason` is one of `no_key`, `provider_error`, `bad_output`, `budget_exceeded`. A fallback is a normal result, not an HTTP error.

Findings with no template appear in `needsHuman` with a reason. They never become proposals.

Errors: `not_found`, `busy`.

### 4.5 GET /api/scans/{id}/agent/stream (Tier 2)

Purpose: send trace entries to the UI as they happen. See section 6.

### 4.6 GET /api/proposals/{id}

Response 200: a `Proposal`. Errors: `not_found`.

### 4.7 PATCH /api/proposals/{id}

Purpose: let a person edit the wording the template uses. Only wording is editable. Nobody hand-edits code.

Request fields:

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `params` | object | Yes | Only keys allowed for the proposal's template: `labelText` for T1 and T5, `altText` for T2. T3 and T4 have no editable wording. Each value is a non-empty string, at most 200 characters, with control characters rejected. |

Behaviour: regenerates the diff and diff hash, sets the status back to `proposed`, and voids any approval token already issued for this proposal. Values are escaped when written into HTML.

Response 200: the updated `Proposal`. Errors: `not_found`, `invalid_request`, `invalid_state` (already applied).

### 4.8 POST /api/proposals/{id}/approve

Purpose: record the person's approval of this exact diff.

Request: no body.

Response 200 fields:

| Field | Type | Notes |
|-------|------|-------|
| `proposalId` | string | |
| `token` | string | Random, single use, shown to the client once |
| `diffHash` | string | The diff this token is bound to |
| `expiresAt` | string | 15 minutes after issue |

Approving again issues a new token and voids the previous one. Errors: `not_found`, `invalid_state` (applied or skipped).

### 4.9 POST /api/proposals/{id}/skip

Purpose: record that the person chose not to apply this proposal. Response 200: the updated `Proposal` with status `skipped`. Errors: `not_found`, `invalid_state`.

### 4.10 POST /api/proposals/{id}/apply

Purpose: apply the approved change to the working copy, re-test, and return the result. This is the only endpoint that writes files.

Request fields:

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `token` | string | Yes | The token from approve |

Server steps, in order:

1. Check the token (exists, not expired, not used, matches the proposal ID and current diff hash). Consume it.
2. Check the scan target is the bundled demo. Otherwise `apply_not_allowed`.
3. Create the working copy if this is the first apply for the scan.
4. Save a snapshot of the files that will change.
5. Run the template. If its target is not found exactly once, `template_mismatch` and nothing is written.
6. Write the result to the working copy only, after the path check.
7. Re-scan the patched page with the same settings as the first scan.
8. Scan the control page in the working copy and compare with its baseline.
9. Compare findings by match key and derive the status.

Response 200: an `ApplyResult` with `status` of `passed`, `partial`, `failed` or `needs_human`, the comparison, the control result, a reason built from facts, and the trace. A `failed` status is a normal result, not an HTTP error.

If the re-scan itself cannot run, the working copy is restored from the snapshot taken in step 4, the proposal is marked `failed`, and the response is a `scan_failed` error.

Errors: `not_found`, `approval_required`, `apply_not_allowed`, `path_not_allowed`, `template_mismatch`, `invalid_state`, `scan_failed`, `browser_unavailable`, `busy`.

### 4.11 POST /api/workspaces/{id}/rollback (Tier 3)

Purpose: restore the previous snapshot of the working copy. Request: no body. Response 200 fields: `workspaceId`, `restoredSnapshot` (number). Errors: `not_found`, `invalid_state` (no earlier snapshot).

### 4.12 GET /api/scans/{id}/export (Tier 2)

Purpose: download a JSON report.

Included: scope (URL, time, engine and version, tags), findings with evidence, labelled AI drafts and the `aiUsed` and model name, proposals and decisions, apply results, coverage and limits.

Excluded, always: approval tokens, API keys, full page source, screenshots and crops, internal file paths outside the working copy.

Response 200 with `Content-Disposition` set to a file download. Errors: `not_found`.

## 5. Static resources

The backend serves the demo sites read-only for the page pane and for scanning.

| Path | Content | Rules |
|------|---------|-------|
| `/sites/original/...` | The bundled sites | Read-only. GET only. |
| `/sites/work/{id}/...` | The patched working copy | GET only. Written only by the apply step. |

Requests that try to leave these folders (path traversal) return 404.

## 6. Streaming (Tier 2)

`GET /api/scans/{id}/agent/stream` returns server-sent events.

| Event name | Data | When |
|------------|------|------|
| `trace` | One `TraceEntry` | Each time a step finishes (or starts, for steps with a duration) |
| `done` | The run ID | The run ended normally or by fallback |
| `error` | `{ code, message }` | The run could not continue |

Rules:

- Entries are sent in `seq` order, and the streamed entries equal the final trace.
- The server sends a periodic keep-alive comment so idle connections stay open.
- An optional `after` query parameter (a `seq` number) lets a reconnecting client skip entries it already has.
- Closing the stream does not cancel the run.

## 7. Validation rules

- Validate every request body, path parameter and query parameter with the Pydantic models. Reject anything unknown.
- `url`: parse, require `http` or `https`, a host, no credentials in the URL, and a length limit. Then apply the URL policy (below).
- URL policy: resolve the host, reject loopback (except the development exception for the bundled demo), private, link-local (including cloud metadata addresses), unique-local and other reserved ranges, for IPv4 and IPv6. Re-check after every redirect, and enforce it in the browser's request handling too.
- Text parameters: trimmed, non-empty, length-limited, control characters rejected, HTML-escaped on output.
- Path parameters: IDs must match the expected opaque format, otherwise `not_found`.
- State checks: a proposal can only be approved while `proposed` or `approved`, and applied only while `approved`.
- The limits in section 9 are enforced on the server, even if the client also checks them.

## 8. Error conventions

Every error response has the same shape: an `error` object with a `code` and a human-readable `message`. The message is plain and short, never a stack trace, file path outside the working copy, or secret.

| Code | HTTP status | Meaning |
|------|-------------|---------|
| `invalid_request` | 422 | Body, parameter or query failed validation |
| `consent_required` | 400 | Authorisation flag missing or false |
| `invalid_url` | 400 | Not a valid `http` or `https` URL |
| `blocked_target` | 403 | URL policy rejected the host |
| `not_found` | 404 | Unknown scan, proposal or workspace |
| `invalid_state` | 409 | Action not allowed in the proposal's current state |
| `needs_human` | 409 | No template exists for this finding |
| `template_mismatch` | 409 | The template could not find its target exactly once |
| `approval_required` | 403 | Token missing, wrong, expired or already used |
| `apply_not_allowed` | 403 | The scan target is not the bundled demo |
| `path_not_allowed` | 403 | File outside the working copy or not on the allowlist |
| `busy` | 429 | Too many operations at once (section 12) |
| `scan_failed` | 502 | The page did not load or the engine failed |
| `browser_unavailable` | 503 | Chromium could not start. The message includes the install command. |
| `internal_error` | 500 | Unexpected failure. Logged server-side with a request ID. |

Not HTTP errors: `model_unavailable` and `budget_exceeded` describe an agent fallback. They appear as `fallbackReason` values and as log lines, and the response is still 200.

The frontend maps every code to a short `System` log line. An unknown code shows a generic line, never raw server text.

## 9. Pagination, filtering and limits

Pagination and server-side filtering are not needed. A scan of one page returns a bounded set, and the UI filters in the browser. Instead, the server enforces limits so responses stay small.

| Limit | Value | Notes |
|-------|-------|-------|
| URL length | 2048 characters | |
| Snippet length | 300 characters | Per finding |
| Findings per scan | 500 | Extra findings are dropped and a `System` trace entry says how many |
| Keyboard walk | 30 stops or 5 seconds | Whichever comes first. `truncated` is set. |
| Editable text value | 200 characters | |
| Trace entries per run | Bounded by the step limits | |

The limits marked as defaults live in one constants module and can be changed without touching the endpoints. The values above that are not from the PRD are proposed defaults and should be confirmed by the team.

## 10. External services and integrations

### 10.1 Model provider (optional)

| Item | Detail |
|------|--------|
| Providers | GitHub Models or Azure OpenAI, through an OpenAI-compatible chat completions interface with tool calling |
| Purpose | Let the agent read evidence through bounded tools, write explanations, and choose templates and parameters |
| Called from | The backend only. Never from the browser. |
| Authentication | Credentials from environment variables, sent in the request headers the provider documents for its API |
| Base URL and model name | From environment variables. Check the provider's current documentation for the right values. Do not guess. |
| Timeouts | 20 seconds per call, 90 seconds per agent run |
| Retries | One retry for network errors, timeouts, HTTP 429 and 5xx, with a short backoff that respects any `Retry-After` header, and only while the run budget allows. These calls are read-only, so a retry cannot duplicate an action. No retry for 4xx other than 429. |
| Budget | 8 turns and 14 tool calls per run. Exceeding it stops the model and runs the built-in agent for what remains. |
| Output handling | Treat all model output as untrusted text. Parse tool calls against a strict schema. Malformed output triggers the fallback. |
| What is sent | Only finding evidence the tools return: rule ID, impact, help text, selector, snippet. Never the full page source, never credentials, never approval tokens. |
| Transparency | The `Show` detail for each agent step displays exactly what was sent and what came back. |

When the model cannot be used, the built-in agent runs, the log says why, and the layout does not change.

### 10.2 Browser and target pages

Chromium is driven locally through Playwright. It makes outbound requests to the page the user chose, subject to the URL policy. The target page's content stays on the machine except for the bounded snippets sent to the model.

### 10.3 Rule engine

axe-core is a local file loaded from `backend/vendor`. It makes no network calls. The version is pinned and reported in every scan.

### 10.4 Web Speech API (Tier 3)

Runs in the browser. No backend call and no data leaves the machine. The text is always shown alongside any speech.

### 10.5 VS Code extension (Tier 3)

If built, it calls the same local endpoints (`POST /api/scans`, proposals) from the user's machine. It adds no endpoints of its own and gets no extra privileges.

## 11. Webhooks

None. AccessPilot neither receives nor sends webhooks. Do not add one. If a future integration needs one, it must verify a signature on the raw body using a shared secret held in the backend environment, reject stale timestamps, deduplicate by event ID, and be documented here first.

## 12. Rate limiting and concurrency

There is one local user, so the goal is to protect the machine and keep results consistent, not to meter usage.

| Rule | Value |
|------|-------|
| Concurrent scans or re-scans | 1 at a time. A second request returns `busy` (429) with a `Retry-After` header. |
| Concurrent applies | 1 per working copy, and not while a scan on that copy is running |
| Agent runs | 1 per scan at a time |
| Scan timeout | Bounded so a hung page cannot block the server. Browser closed in `finally` on timeout. |
| Outbound model calls | Within the run budget. On 429 from the provider, honour `Retry-After` once, then fall back. |

Browser launches are serialised so no leftover processes accumulate (20 scans must leave none).

## 13. Idempotency and duplicate prevention

| Operation | Behaviour |
|-----------|-----------|
| `POST /api/scans` | Not idempotent. Each call is a new scan. |
| `POST /approve` | Each call voids the previous token and issues a new one |
| `POST /apply` | The token is consumed on first use. A repeat with the same token returns `approval_required` and changes nothing. |
| `POST /skip` | Repeating returns the same skipped proposal |
| `PATCH` | Repeating with the same values gives the same diff and hash |
| Model calls | Read-only, so a single retry is safe |

## 14. Environment variables

Set in the backend environment. `.env.example` lists every one with a placeholder and a comment. The real `.env` is never committed.

| Variable | Required | Default | Secret | Purpose |
|----------|----------|---------|--------|---------|
| `AI_PROVIDER` | No | `none` | No | `github_models`, `azure_openai` or `none` |
| `AI_BASE_URL` | If a provider is set | | No | Provider endpoint. Check the provider's documentation. |
| `AI_API_KEY` | If a provider is set | | **Yes** | Provider credential |
| `AI_MODEL` | If a provider is set | | No | Model or deployment name |
| `AI_API_VERSION` | Azure only | | No | Version string Azure's API requires |
| `AI_CALL_TIMEOUT_S` | No | `20` | No | Per model call |
| `AI_RUN_TIMEOUT_S` | No | `90` | No | Per agent run |
| `AGENT_MAX_TURNS` | No | `8` | No | Model turns per run |
| `AGENT_MAX_TOOL_CALLS` | No | `14` | No | Tool calls per run |
| `BACKEND_HOST` | No | `127.0.0.1` | No | Interface the API listens on |
| `BACKEND_PORT` | No | `8000` | No | Port |
| `FRONTEND_ORIGIN` | No | Local Vite dev origin | No | The one allowed CORS origin |
| `ALLOW_LOOPBACK` | No | `true` | No | Development exception so the bundled demo can be scanned |

Frontend (non-secret only): `VITE_API_BASE_URL`.

Startup behaviour: if `AI_PROVIDER` is set but a required companion variable is missing, start in built-in mode and log which variable is missing. Never print the value of a secret.

## 15. Data privacy

- Page source is never stored. Findings keep a snippet of at most 300 characters.
- Screenshots and element crops (Tier 3) exist in memory only and are never exported.
- Only bounded finding evidence is sent to a model provider, and only when a model is configured. The UI says when a model is in use, and `Show` displays what was sent.
- Tokens, keys and full URLs with query strings are not written to logs. Logs record IDs, rule IDs, durations and error codes.
- Exports contain no secrets, tokens or page source.
- Everything is in memory and disappears when the server stops. Temporary working copies are deleted on exit.
- The authorisation flag exists so people only scan pages they are permitted to test. The server enforces it on every scan.

## 16. Failure handling

| Failure | What happens |
|---------|--------------|
| No model, no key, outage, timeout, bad output, or budget exceeded | Built-in agent runs. `fallbackReason` is set. A `System` log line explains it. HTTP 200. |
| Chromium cannot start | `browser_unavailable` with the install command |
| Page fails to load or the engine errors | `scan_failed`. No empty scan is stored as a success. |
| Template target not found exactly once | `template_mismatch`. Nothing written. The finding becomes Needs a person. |
| Re-scan fails after a patch | Restore the snapshot, mark the proposal failed, return `scan_failed` |
| Patch makes things worse | Status `failed`, with introduced findings or control regressions listed |
| Token wrong, expired or reused | `approval_required`. Nothing changes. |
| Second heavy request while one runs | `busy` with `Retry-After` |
| Unexpected exception | `internal_error` with a request ID. Details are logged server-side only. |
| API unreachable from the UI | The frontend shows a `System` line: the API cannot be reached and the backend should be running on port 8000 |

Every failure produces a trace entry or log line. Nothing fails silently, and no failure is shown as a success.

## 17. Changes needed in other documents

This file introduces a few items that `architecture.md` and `PRD.md` do not yet list. Update them in the same change that implements them.

1. **Error codes** to add to `architecture.md` section 6: `invalid_request`, `invalid_state`, `busy`, `internal_error`.
2. **`Finding.box`** (optional, Tier 2) so the page overlay can draw boxes: an object with `x`, `y`, `width`, `height` in page coordinates plus the viewport size. `architecture.md` mentions bounding boxes in the frontend section but does not define the field.
3. **`GET /api/health` fields** `browserAvailable`, `modelConfigured`, `modelName`, `engineVersion`.
4. **Stream `after` parameter** on the agent stream.
5. **Environment variables** `AI_API_VERSION`, `AI_CALL_TIMEOUT_S`, `AI_RUN_TIMEOUT_S`, `AGENT_MAX_TURNS`, `AGENT_MAX_TOOL_CALLS`, `BACKEND_HOST`, `BACKEND_PORT`, `FRONTEND_ORIGIN` to add to `.env.example`.

## 18. Out of scope

User accounts, API keys for clients, roles, pagination, a scans list endpoint, webhooks, a database, background job queues, multi-user sharing, and any endpoint that applies changes to a site other than the bundled demo.
