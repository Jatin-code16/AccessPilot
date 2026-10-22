# AccessPilot: Architecture

**Version:** 1.0. Companion to `PRD.md` (what to build) and `design.md` (how the UI looks). This file says how the system is put together and what each part may and may not do.

Stack: Python FastAPI backend, Playwright (Python) with Chromium, React with Vite and TypeScript frontend. The model is optional and is reached through an OpenAI-compatible client. State is in memory. Everything runs locally.

---

## 1. System overview

```
+----------------------------- Browser (React UI) -----------------------------+
|  Page pane (iframe + overlay)        |        Log pane (lines + cards)        |
+--------------------+--------------------------------------------^-------------+
                     | REST (JSON), SSE for trace                 |
+--------------------v--------------------------------------------+-------------+
|                        FastAPI backend (port 8000)                             |
|                                                                                |
|  API layer: routes, validation, one error shape                                |
|     |                                                                          |
|  +--v-------+   +----------+   +-----------+   +-------------------+          |
|  | Scan     |   | Agent    |   | Repair    |   | Verifier          |          |
|  | service  |   | service  |   | engine    |   | (deterministic)   |          |
|  | Playwright|  | LLM loop |   | templates |   | re-scan, compare, |          |
|  | + axe    |   | + built-in|  | approval, |   | control check,    |          |
|  | + keyboard|  | fallback |   | apply     |   | status            |          |
|  +----+-----+   +----+-----+   +-----+-----+   +---------+---------+          |
|       +--------------+---------------+-------------------+                    |
|              In-memory store  |  temp working copies on disk                   |
+-------+---------------------------------------------+-------------------------+
        | drives                                      | serves
+-------v----------------+                  +---------v-------------------------+
| Headless Chromium      |<-----------------+ Static mounts                     |
+------------------------+                  |  /sites/original  (read-only)     |
                                            |  /sites/work/{id}  (patched copy) |
Optional: LLM provider (GitHub Models or    +-----------------------------------+
Azure OpenAI). Never required.
```

Three of the four services are deterministic. Only the agent service can call a model, and the model cannot write files or set a status.

## 2. Trust boundaries

These are the rules the whole design rests on. Any change that weakens one needs a decision from the team, not a quiet code edit.

| Boundary | How it is enforced |
|----------|--------------------|
| The model proposes. It never applies. | Agent tools are read-only except `draft_repair`, which returns a proposal object and writes nothing. |
| The model never writes patches. | It picks a template (T1 to T5) and supplies parameters. Code generates the diff. |
| A human approves the exact change. | Approval makes a single-use token tied to proposal ID and diff hash. Editing the wording voids it. |
| The original is never touched. | Apply works only inside a copied working directory. A path allowlist rejects everything else. |
| Status comes from evidence. | The verifier compares findings from two scans. Model output never enters the status code path. |
| The tool does not claim compliance. | Status words are fixed (section 9). No score is computed anywhere. |

## 3. Repository layout

```
accesspilot/
  .github/
    copilot-instructions.md      # rules for Copilot (see that file)
  docs/
    PRD.md  architecture.md  design.md  COPILOT_LOG.md
  backend/
    app/
      main.py                    # FastAPI app, static mounts, CORS
      api/                       # scans.py, agent.py, proposals.py, report.py
      core/                      # config.py, errors.py, url_policy.py, store.py, trace.py
      scan/                      # browser.py, axe_runner.py, keyboard.py, normalize.py
      agent/                     # loop.py, tools.py, prompts.py, fallback.py, llm.py
      repair/                    # templates.py, proposals.py, approval.py, apply.py, workspace.py
      verify/                    # match.py, compare.py, status.py
      knowledge/                 # explanations.py, statutes.py (P2, filled by a person)
    vendor/axe.min.js            # pinned version, committed
    tests/
    requirements.txt
  sites/
    golden/                      # index.html, golden.css
    control/                     # control.html (shares shared.css with golden)
    shared.css
  frontend/
    src/
      api/                       # typed client, SSE hook
      state/                     # one session store
      components/                # AppShell, PagePane, Log, LogLine, YourTurnCard,
                                 # NeedsPersonCard, ResultCard, StageDots, CoverageView
      styles/                    # tokens.css (from design.md)
    package.json
  scripts/
    start.ps1  start.sh  self_audit.py
  .env.example
  README.md
```

## 4. Data models

Types are shown in TypeScript form for clarity. The backend uses Pydantic models with the same field names (camelCase in JSON). The frontend types must match the JSON exactly.

```ts
type Impact = "critical" | "serious" | "moderate" | "minor";
type Actor  = "scanner" | "agent" | "you" | "retest" | "system";

interface Finding {
  id: string;                    // stable within one scan
  matchKey: string;              // ruleId + "|" + target selector (used to compare scans)
  fingerprint: string;           // hash of ruleId + selector + snippet (evidence only)
  source: "axe" | "keyboard";
  kind: "violation" | "incomplete";
  ruleId: string;                // exactly as returned by the engine
  impact: Impact | null;
  help: string;
  helpUrl: string | null;
  tags: string[];
  wcag: string[];                // criteria derived from engine tags
  target: string;                // CSS selector
  snippet: string;               // 300 characters at most
  explanation: { who: string; blockedFrom: string; why: string };
  template: "T1" | "T2" | "T3" | "T4" | "T5" | null;
  needsHuman: boolean;
}

interface TraceEntry {
  seq: number;
  actor: Actor;
  name: string;                  // e.g. "load_page", "list_findings"
  summary: string;               // 8 words or fewer, shown in the log
  inputSummary?: string;         // shown under "Show"
  outputSummary?: string;
  durationMs?: number;
  ok: boolean;
  errorCode?: string;
  startedAt: string;             // ISO 8601
}

interface Scan {
  id: string;
  url: string;
  workingCopyId: string | null;
  startedAt: string;
  durationMs: number;
  title: string;
  engine: { name: "axe-core"; version: string };
  findings: Finding[];
  passCount: number;
  keyboardWalk?: { stops: Stop[]; loopDetected: boolean; truncated: boolean };
  coverage: { ran: string[]; didNotRun: string[]; needsPerson: string[] };
  trace: TraceEntry[];
}

interface Stop { index: number; selector: string; role: string; name: string; repeat: boolean }

interface Proposal {
  id: string;
  scanId: string;
  findingId: string;
  template: "T1" | "T2" | "T3" | "T4" | "T5";
  status: "proposed" | "approved" | "rejected" | "skipped" | "applied" | "failed";
  rationale: string;
  risk: "low" | "medium";
  files: string[];               // paths inside the working copy
  params: Record<string, string>;
  diff: string;                  // unified diff generated by code
  diffHash: string;
  proposedBy: "agent" | "builtin";
}

interface ApplyResult {
  proposalId: string;
  beforeScanId: string;
  afterScanId: string;
  comparison: { resolved: string[]; remaining: string[]; introduced: string[] }; // match keys
  control: { passed: boolean; newFindings: string[] };
  status: "passed" | "partial" | "failed" | "needs_human";
  reason: string;
  trace: TraceEntry[];
}

interface AgentRun {
  id: string;
  scanId: string;
  aiUsed: boolean;
  model: string | null;
  fallbackReason: string | null; // "no_key" | "provider_error" | "bad_output" | "budget_exceeded" | null
  explanations: Record<string, string>;
  proposals: Proposal[];
  needsHuman: { findingId: string; reason: string }[];
  trace: TraceEntry[];
}
```

Status mapping to UI words: `passed` is "Passed", `partial` is "Partly passed", `failed` is "Failed", `needs_human` is "Needs a person".

## 5. Backend services

### 5.1 Scan service

Order of work for `POST /api/scans`:

1. **Validate.** Check consent, scheme, and URL policy (section 5.5). Return a typed error, never a stack trace.
2. **Launch** headless Chromium through Playwright. Block requests to disallowed ranges at the browser level too, so redirects cannot escape the policy.
3. **Load** the page and wait for the load event. Record a trace entry with the real duration.
4. **Inject** the vendored `axe.min.js` from disk (never from a CDN) and run it with these tags: `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`, `best-practice`. Record the engine version reported by the page.
5. **Normalise** violations and incomplete items into `Finding` objects, one per affected node. Compute `matchKey` and `fingerprint`. Attach explanations from `knowledge/explanations.py`. Mark the template if the rule has one.
6. **Keyboard walk** (Tier 2): press Tab up to 30 times or 5 seconds. For each stop record selector, role, accessible name (approximation). Flag a repeated element as a loop. Flag elements with a click handler that never received focus.
7. **Close** the browser in a `finally` block. Always.
8. **Build coverage** from what actually ran. The `didNotRun` list is a fixed list of things this tool does not test (captions, reading order, content meaning, real screen readers).

A page that fails to load returns `scan_failed` with the reason in the log. It does not return an empty successful scan.

### 5.2 Agent service

**Built-in agent (build first).** A plain function that loops over findings, writes the explanation from the knowledge table, and for findings with a template calls the same `draft_repair` code the model would use, with default parameters. For findings with no template it records a needs-human entry with a reason. It is complete on its own. Every fallback is logged with a reason.

**Model agent (Tier 2).** OpenAI-style tool calling.

| Tool | Reads or writes | Returns |
|------|-----------------|---------|
| `list_findings()` | Reads | Finding IDs, rule, impact, target |
| `get_evidence(findingId)` | Reads | Snippet, help text, explanation |
| `list_templates()` | Reads | T1 to T5 with their parameters |
| `draft_repair(findingId, params)` | Writes a proposal object only | Proposal with diff and hash |
| `mark_needs_human(findingId, reason)` | Writes a note only | Acknowledgement |
| `submit_report(summary)` | Writes a summary only | Acknowledgement |

Limits: 8 turns, 14 tool calls, 90 seconds per run, 20 seconds per model call. On any limit, or on malformed output, stop, run the built-in agent for what remains, and set `fallbackReason`.

Guards:

- `draft_repair` rejects any finding with no template and returns `needs_human`.
- The model's text is stored as an explanation labelled Draft. It is never parsed for status.
- The model has no tool that writes files, runs commands, or fetches URLs.
- Prompts instruct the model to use only rule IDs and selectors returned by the tools, and to say "unknown" when it does not know.

**Configuration.** `AI_PROVIDER`, `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL` from environment. If any is missing, the agent runs in built-in mode and says so. Check the provider's current documentation for the exact base URL and model names. Do not guess them.

### 5.3 Repair engine

Each template is a pure function `(source: str, params) -> (new_source: str, unified_diff: str)`. No file I/O inside the template.

| T | Finds target by | Edit |
|---|-----------------|------|
| T1 | `id` of the input | Insert `<label for="{id}">{labelText}</label>` immediately before the input. Fail if a label for that `id` already exists. |
| T2 | `id` of the image | Add or replace the `alt` attribute. |
| T3 | The stylesheet rule matching the element's class or id | Replace the `color` value with a computed passing colour (see below). |
| T4 | The opening `<html>` tag | Add `lang="{lang}"` if absent. |
| T5 | `id` of the button | Add or replace `aria-label`. |

Rules for every template:

- Find the target exactly once. Zero or several matches raise `template_mismatch`.
- Make the smallest possible edit. Do not reformat the file.
- Escape parameter values for HTML attributes and text.
- Return the same output for the same inputs. The diff hash depends on it.

**T3 colour computation.** Compute the WCAG contrast ratio from relative luminance. Starting from the current text colour, darken (or lighten on dark backgrounds) in small steps until the ratio is at least 4.5 for normal text. Keep the hue. Unit-test this function with known pairs.

**Workspace.** On the first approval for a scan, copy `sites/` into `work/{id}/`. This copy contains the Golden Site, the control page and `shared.css`. The control page therefore really can regress when a stylesheet change goes wrong. Later approvals patch the same copy. Before each apply, snapshot the files that will change into `work/{id}/.snapshots/{n}/`.

**Allowlist.** Only files named in the proposal, inside `work/{id}/`, with extension `.html` or `.css`. Resolve the path and confirm it stays inside the working directory. Anything else raises `path_not_allowed`.

**Approval.** `POST /api/proposals/{id}/approve` returns a random token stored in memory with the proposal ID, diff hash, and a 15-minute expiry. `POST /api/proposals/{id}/apply` needs that token, checks it matches the current diff hash, consumes it, and refuses reuse.

### 5.4 Verifier

Deterministic. No model.

1. Re-scan the patched page in the working copy with the same settings as the first scan.
2. Compare by `matchKey`: **resolved** (in before, not in after), **remaining** (in both), **introduced** (in after, not in before).
3. Scan the control page in the working copy. Compare to the control baseline taken from the same working copy before the apply. Any new `matchKey` is a regression.
4. Derive the status:

| Condition | Status |
|-----------|--------|
| Target finding resolved, nothing introduced, control clean | `passed` |
| Some targeted findings resolved, others remain, nothing introduced, control clean | `partial` |
| Target still present, or anything introduced, or control regressed | `failed` |
| Finding has no template | `needs_human` |

Every result includes a reason string built from these facts. The reason names the counts and the rule IDs. It is never written by a model.

### 5.5 URL policy

- Allow `http` and `https` only.
- Resolve the host and reject loopback (except the development exception for the bundled demo origin), private ranges (10/8, 172.16/12, 192.168/16), link-local (169.254/16, including cloud metadata addresses), unique-local and other reserved ranges, for IPv4 and IPv6.
- Re-check after redirects.
- Applying a patch is allowed only when the scan's URL is the bundled demo working copy.

## 6. API

JSON in and out. One error shape: `{ "error": { "code": "...", "message": "..." } }`.

| Method | Path | Purpose | Tier |
|--------|------|---------|------|
| GET | `/api/health` | Status, whether a model is configured | 1 |
| POST | `/api/scans` | Body `{url, consent}`. Returns `Scan`. | 1 |
| GET | `/api/scans/{id}` | Fetch a scan | 1 |
| POST | `/api/scans/{id}/agent` | Run the agent (or built-in). Returns `AgentRun`. | 1 |
| GET | `/api/scans/{id}/agent/stream` | SSE of trace entries | 2 |
| GET | `/api/proposals/{id}` | Proposal with diff | 1 |
| PATCH | `/api/proposals/{id}` | Edit allowed parameters. Regenerates diff and voids any token. | 1 |
| POST | `/api/proposals/{id}/approve` | Returns single-use token | 1 |
| POST | `/api/proposals/{id}/skip` | Mark skipped | 1 |
| POST | `/api/proposals/{id}/apply` | Body `{token}`. Applies, re-scans, verifies. Returns `ApplyResult`. | 1 |
| POST | `/api/workspaces/{id}/rollback` | Restore previous snapshot | 3 |
| GET | `/api/scans/{id}/export` | JSON report | 2 |

### Error codes (the complete list)

| Code | Meaning |
|------|---------|
| `consent_required` | Authorisation flag missing |
| `invalid_url` | Not a valid `http` or `https` URL |
| `blocked_target` | URL policy rejected the host |
| `scan_failed` | Page did not load or the engine failed |
| `browser_unavailable` | Chromium could not start (message includes the install command) |
| `not_found` | Unknown scan, proposal or workspace |
| `needs_human` | No template for this finding |
| `template_mismatch` | Template could not find its target exactly once |
| `path_not_allowed` | File outside the working copy or not on the allowlist |
| `approval_required` | Missing, wrong, expired or reused token |
| `apply_not_allowed` | Scan target is not the bundled demo |
| `model_unavailable` | No key, outage or bad output (not an HTTP failure: the fallback runs) |
| `budget_exceeded` | Agent hit a limit (the fallback runs) |

Do not add codes without adding them here and in the frontend's error map.

## 7. Frontend architecture

- **State:** one store holding the current scan, agent run, proposals, results, and the ordered log entries. Components read from it. API calls and SSE events update it.
- **Log entries come from trace entries.** The frontend does not generate log lines of its own, apart from `System` lines for errors it observes (for example the API being unreachable).
- **Components:** `AppShell`, `PagePane`, `Log`, `LogLine`, `YourTurnCard`, `NeedsPersonCard`, `ResultCard`, `StageDots`, `CoverageView`. See `design.md` for behaviour and look.
- **Page pane:** an `<iframe>` with `sandbox` set, pointing at `/sites/original/golden/` or `/sites/work/{id}/golden/`. The overlay is positioned from element rectangles reported by the scan (selector to bounding box). The overlay is `aria-hidden`.
- **Typed client:** one module with a function per endpoint. Types mirror section 4. Errors are parsed into the shape in section 6.
- **No local storage.** State is per page load.

## 8. Core flow

```
User        UI           API          Scan        Agent       Repair     Verifier
 | URL+ok    |            |            |           |           |           |
 |---------->| POST /scans|            |           |           |           |
 |           |----------->| validate-->| browser, axe, normalise            |
 |           |<-----------| Scan{findings, trace}                          |
 | Run agent | POST /agent|            |           |           |           |
 |---------->|----------->|-------------------------> tools / builtin       |
 |           |<-----------| AgentRun{proposals(diff), trace}               |
 | Approve   | POST /approve ------------------------------> token         |
 |---------->| POST /apply  ------------------------------> copy, snapshot, patch
 |           |            |-------------------------------------------------> re-scan, compare, control
 |           |<-----------| ApplyResult{status, counts, trace}             |
 | sees result card in the log                                              |
```

## 9. Status words and wording guard

The backend returns only the four status values in section 4. The frontend maps them to the four UI words. A test scans UI strings and fails on any of these: "compliant", "certified", "conformant", "% accessible", "accessibility score", "fully accessible".

## 10. Failure handling

| Failure | Behaviour |
|---------|-----------|
| No key, outage, bad JSON, timeout | Built-in agent runs. Log line: `System  No AI model. Using built-in guidance.` plus reason. |
| Chromium fails to start | `browser_unavailable` with the install command. |
| Template cannot find its target | `template_mismatch`. Finding becomes Needs a person. |
| Bad patch | Re-scan still shows the finding. Status `failed`. |
| Patch introduces a new finding | Status `failed`. New match keys listed. |
| Control page regresses | Status `failed`. Control findings listed. |
| Token missing, reused or stale | `approval_required`. Nothing changes. |
| Finding has no template | Needs a person card. No Approve button. |
| Page fails to load | `scan_failed`. No empty scan returned. |

## 11. Testing

Backend tests use pytest. Frontend checks use a Playwright run against the built UI.

| Area | Tests |
|------|-------|
| URL policy | Each blocked range, redirects, allowed loopback exception |
| Scan | Golden Site returns D01 to D05 rule IDs. Browser always closed (run 20 scans, count processes). |
| Normalise | Match key and fingerprint are stable across two scans of the same page |
| Templates | Each of T1 to T5: expected diff, idempotent output, `template_mismatch` on zero and on multiple targets |
| Contrast | Known colour pairs give known ratios. T3 output reaches 4.5. |
| Approval | Single use, wrong diff hash, expiry, void after edit |
| Workspace | Original files hash-identical after apply. Path escape attempts raise `path_not_allowed`. |
| Verifier | Fixtures for passed, partial, failed (bad patch), failed (introduced), failed (control regression) |
| Agent | Fallback on no key, malformed output, timeout and budget overrun. Tools cannot write files. |
| Export | No token, key or page source in the JSON |
| Wording | UI strings pass the guard in section 9 |
| Self-audit | `self_audit.py` reports zero serious or critical findings, light and dark |

## 12. Configuration and running

`.env.example` lists every variable with a placeholder and a comment. The real `.env` is never committed.

```
AI_PROVIDER=          # github_models | azure_openai | none
AI_BASE_URL=          # check the provider's docs
AI_API_KEY=
AI_MODEL=
ALLOW_LOOPBACK=true   # development exception for the bundled demo
```

Setup commands go in `README.md` and must be tested on a second machine. Typical commands: create a virtual environment, `pip install -r requirements.txt`, `python -m playwright install chromium`, `npm install` in `frontend`, then the start script.

## 13. Known gotchas

- **Playwright on Windows with Uvicorn.** Playwright launches a subprocess, which needs the Proactor event loop on Windows. Running Uvicorn with `--reload` can switch loops and raise `NotImplementedError`. Start the backend without `--reload` during demos, or set the event-loop policy explicitly, and test it on the demo machine.
- **Selectors versus source.** Axe selectors describe the rendered DOM, which may differ from the source file. Templates find targets by stable `id`, not by the selector string.
- **Shared stylesheet.** The control page only works as a regression check if it shares `shared.css` with the Golden Site and both are in the working copy.
- **Contrast on dynamic backgrounds.** Axe may report contrast as "incomplete" when it cannot decide. Show incomplete items as Needs a person, not as failures.
- **Vendored engine.** Load `axe.min.js` from disk. A CDN load fails offline and silently changes versions.
- **Iframe and framing headers.** The bundled sites are served by us, so framing works. Real third-party pages often block framing. The read-only scan of a real page (if shown) uses a screenshot, not the iframe.

## 14. Build sequence mapped to files

1. `sites/golden`, `sites/control`, `sites/shared.css`
2. `scan/` and `POST /api/scans`
3. `knowledge/explanations.py` and the Log UI
4. `repair/templates.py` with unit tests, then `agent/fallback.py`
5. `repair/approval.py`, `workspace.py`, `apply.py`
6. `verify/` and the Result card
7. `agent/llm.py` and `loop.py`, then SSE
8. Keyboard walk, coverage, overlay, export, self-audit
9. Tier 3 items in the order given in `PRD.md`
