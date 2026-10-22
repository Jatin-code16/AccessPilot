# AccessPilot Frontend–Backend Integration Contract

This file is the handoff agreement between the frontend and backend work.

The source of truth for endpoint details is [`API.md`](./API.md). The source
of truth for shared objects is [`architecture.md`](./architecture.md), section
4. This file explains how the two workstreams connect without changing those
documents.

## 1. Scope

This contract supports the Tier 1 core loop:

```text
scan -> explain -> draft -> approve -> apply -> re-test
```

It covers:

- the local connection between Vite and FastAPI,
- ownership boundaries,
- shared JSON conventions,
- endpoint handoff points,
- frontend states,
- mock data rules,
- integration checks.

It does not add endpoints, error codes, fields, or dependencies.

## 2. Ownership

| Area | Backend owner | Frontend owner |
|------|---------------|----------------|
| Pydantic request and response models | Yes | No |
| Endpoint paths, methods, status codes | Yes | Consume only |
| Error mapping and server validation | Yes | Render the error |
| In-memory store | Yes | No |
| Browser scanning and axe execution | Yes | No |
| Agent and fallback behavior | Yes | No |
| Repair templates and diff generation | Yes | No |
| Approval and apply authorization | Yes | No |
| Verifier status | Yes | Display only |
| React components and layout | No | Yes |
| Frontend state store | No | Yes |
| Typed API client | Contract consumer | Yes |
| Design tokens and UI wording | No | Yes |
| End-to-end integration tests | Shared | Shared |

Neither workstream should edit the other workstream's implementation files
without coordinating first.

## 3. Shared invariants

Both sides must preserve these rules:

1. JSON field names use camelCase.
2. Times are ISO 8601 UTC strings.
3. Durations are integer milliseconds in `durationMs` fields.
4. IDs are opaque strings. The frontend must not parse them.
5. Optional fields are omitted unless the type explicitly permits `null`.
6. Unknown request fields are rejected by the backend.
7. Errors use exactly:

   ```json
   {
     "error": {
       "code": "invalid_request",
       "message": "Human-readable explanation"
     }
   }
   ```

8. The frontend must not calculate, infer, or override verifier status.
9. The frontend must not send approval tokens anywhere except the apply
   request that requires the token.
10. The frontend must not receive or expose model-provider credentials.
11. Trace entries shown in the log must come from backend trace data. The
    frontend must not invent progress or timings.

## 4. Local development connection

The documented local defaults are:

| Service | Address | Responsibility |
|---------|---------|----------------|
| FastAPI backend | `http://127.0.0.1:8000` | `/api/*` and static demo resources |
| Vite frontend | The configured frontend origin | React application |

The backend must bind to loopback by default and allow only the configured
frontend origin through CORS. The frontend stores only the non-secret API
base URL.

The frontend must call the backend through one typed client in
`frontend/src/api`. Components must not call `fetch` directly.

Recommended client shape:

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
```

`VITE_API_BASE_URL` is a non-secret value. No provider key or approval token
may be placed in a Vite environment variable.

## 5. Endpoint handoff table

The following table is an integration map, not a replacement for
[`API.md`](./API.md).

| Frontend action | Request | Expected success | Frontend stores |
|-----------------|---------|------------------|-----------------|
| Load health | `GET /api/health` | `200` health object | Browser/model availability |
| Start scan | `POST /api/scans` | `201` `Scan` | Current scan and trace |
| Refresh scan | `GET /api/scans/{id}` | `200` `Scan` | Current scan and trace |
| Run agent | `POST /api/scans/{id}/agent` | `200` `AgentRun` | Proposals, explanations, needs-person items, trace |
| Read proposal | `GET /api/proposals/{id}` | `200` `Proposal` | Current proposal |
| Edit wording | `PATCH /api/proposals/{id}` | `200` updated `Proposal` | Replace proposal and clear old approval |
| Approve proposal | `POST /api/proposals/{id}/approve` | `200` approval response | Approval token only in memory |
| Skip proposal | `POST /api/proposals/{id}/skip` | `200` `Proposal` | Updated proposal |
| Apply proposal | `POST /api/proposals/{id}/apply` | `200` `ApplyResult` | Result and returned trace |

Tier 2 endpoints must not be wired into the Tier 1 UI before the Tier 1
exit test passes.

## 6. Request rules

### Scan

```json
{
  "url": "http://127.0.0.1:8000/sites/original/golden/index.html",
  "consent": true
}
```

The frontend must:

- send `consent: true` only after the person explicitly confirms
  authorization;
- send an absolute `http` or `https` URL;
- use the bundled Golden Site for the apply flow;
- display server errors instead of converting them into an empty scan.

### Agent

The request body is optional. When supplied, `mode` must be `auto` or
`builtin`. The frontend must not send provider configuration or model
credentials.

### Wording edit

Only the wording parameters allowed by the proposal template may be sent.
The frontend must not send source code or a hand-edited diff.

Allowed parameters are defined by [`API.md`](./API.md), section 4.7:

- `labelText` for T1 and T5;
- `altText` for T2;
- no editable wording for T3 and T4.

### Approval and apply

Approval is tied to the exact current `diffHash`. If the proposal changes,
the frontend must replace its proposal data and discard the old approval.

The frontend must not retry approval or apply automatically. These are
single-use or write operations.

## 7. Frontend state model

The frontend should keep one session store with these conceptual values:

```ts
type WorkbenchStage = "scan" | "review" | "decision" | "retest";
type RequestState = "idle" | "loading" | "ready" | "error";

interface SessionState {
  stage: WorkbenchStage;
  scan: Scan | null;
  agentRun: AgentRun | null;
  activeProposal: Proposal | null;
  approvalToken: string | null;
  applyResult: ApplyResult | null;
  requestState: RequestState;
  error: { code: string; message: string } | null;
}
```

The concrete shared object definitions remain in
[`architecture.md`](./architecture.md), section 4. The frontend should
import or reproduce those types exactly, including enum values and
nullability.

State transitions:

```text
idle
  -> scanning
  -> scan_ready
  -> agent_running
  -> decision_required
  -> approving
  -> applying
  -> result
```

An error returns to a visible error state with the server's error code and
message. It must not look like a successful empty result.

## 8. Rendering rules

The frontend renders backend evidence as follows:

| Backend data | UI surface |
|--------------|------------|
| `TraceEntry` | One ordered log entry |
| `Finding` | Scanner detail and finding explanation |
| `Proposal` | Draft / Your turn card |
| `needsHuman` item | Needs a person card |
| `ApplyResult` | Result card |
| `coverage` | Coverage view when that feature is enabled |
| `error.code` | System error line and accessible error message |

The frontend must:

- show `Draft` for unapproved AI output;
- show status words exactly as defined by the verifier;
- show real durations supplied by the backend;
- preserve raw detail behind a keyboard-accessible disclosure;
- never show scores, percentages, or compliance claims;
- never hide a `Needs a person` item;
- keep overlay graphics `aria-hidden="true"` because the log is the text
  alternative.

## 9. Mocking during parallel development

Until the backend is available, the frontend may use local fixtures with the
same shapes as the backend models.

Rules for fixtures:

1. Fixtures live only in the frontend test or development fixture location.
2. Fixture field names and enum values must match the architecture exactly.
3. Fixtures must not invent endpoints, statuses, rule IDs, or model names.
4. Fixtures must be replaced by API responses before the integration check.
5. A fixture must never be used to claim that a real scan or apply occurred.
6. Approval tokens in fixtures must be clearly test-only and must never be
   sent to a real backend.

When a response shape changes, update the backend model and the relevant
frontend type together, then update the API documentation if the public
contract changed.

## 10. Conflict-prevention workflow

Use this workflow for every shared-contract change:

1. Discuss the proposed change before editing a shared type or endpoint.
2. Confirm whether it changes `API.md`, `architecture.md`, or both.
3. Backend updates the Pydantic model and API behavior.
4. Frontend updates the typed client and state mapping.
5. Both sides run their focused tests.
6. Run one local integration check against the real backend.
7. Do not silently add fallback fields or accept alternate spellings.

Safe parallel file ownership:

| Backend work | Frontend work |
|--------------|---------------|
| `backend/` | `frontend/` |
| `sites/` | Frontend tests and styles |
| Backend tests | Frontend components and state |
| Backend configuration | Frontend typed client |

Shared files requiring coordination:

- [`API.md`](./API.md)
- [`architecture.md`](./architecture.md)
- [`PRD.md`](./PRD.md)
- [`design.md`](./design.md)
- [`AGENTS.md`](../AGENTS.md)
- [`docs/copilot-instructions.md`](./copilot-instructions.md)

## 11. Integration checklist

Before declaring the work connected:

- [ ] Backend answers `GET /api/health`.
- [ ] Frontend uses one API client and no component calls `fetch`.
- [ ] Backend CORS allows only the configured frontend origin.
- [ ] Scan request includes explicit consent.
- [ ] Scan response renders findings and trace entries.
- [ ] Agent response renders proposals and needs-person items.
- [ ] Proposal diff is displayed exactly as returned.
- [ ] Wording edits call `PATCH` and replace the proposal.
- [ ] Approval token is kept in memory only.
- [ ] Apply uses the current token and proposal.
- [ ] Result status is displayed from `ApplyResult` only.
- [ ] Errors use the backend `{ error: { code, message } }` shape.
- [ ] No secret, source document, token, score, or invented timing appears
      in the UI or logs.
- [ ] The Tier 1 offline core-loop test passes three times in a row.

## 12. Change log

This file records the integration agreement, not individual development
activity. Add an entry only when the shared contract itself changes.

| Date | Change | Owners |
|------|--------|--------|
| 2026-10-22 | Initial frontend–backend handoff contract | Frontend and backend |
