# PROMPTS.md

Task prompts for the AI coding agent, adapted to AccessPilot. Paste one into the agent when you reach that kind of work. They assume `AGENTS.md`, `docs/CONTEXT.md`, `docs/PRD.md`, `docs/architecture.md`, `docs/API.md` and `docs/design.md` are in the repository.

There is no `DATABASE.md`. The product has no database, so wherever a generic prompt would mention one, use `docs/architecture.md` section 4 (data models) and the in-memory store.

Fill in the bracketed parts before pasting.

---

## 1. External service integration

### 1a. Ready to use: model provider for the agent (Tier 2)

```
You are a senior integration engineer experienced in building reliable production integrations.

CONTEXT:
Follow docs/API.md (section 10.1 and section 14), docs/architecture.md (section 5.2), and AGENTS.md. This is requirement FR-20 in docs/PRD.md. The built-in agent already works without a model and must keep working.

TASK:
Integrate the optional model provider (GitHub Models or Azure OpenAI, through an OpenAI-compatible chat completions interface with tool calling) so the agent can read evidence through the bounded tools, write explanations labelled Draft, and choose templates and parameters.

Implement:
- Configuration from environment variables only (AI_PROVIDER, AI_BASE_URL, AI_API_KEY, AI_MODEL, AI_API_VERSION for Azure, and the timeout and budget variables). If anything required is missing, start in built-in mode and log which variable is missing, never its value.
- A single client module used by the agent loop and nothing else.
- Tool calling with the tools defined in docs/architecture.md section 5.2 and strict schema validation of every tool call and every argument.
- Limits: 8 turns, 14 tool calls, 90 seconds per run, 20 seconds per call, all configurable.
- Timeouts, and one retry only for network errors, timeouts, HTTP 429 and 5xx, honouring Retry-After and the run budget. No retry for other 4xx.
- Fallback to the built-in agent on no key, provider error, malformed output or budget exceeded. Set fallbackReason and log the reason.
- Trace entries for every model call and tool call, with real durations, and a "Show" payload that displays exactly what was sent and received.
- Sending only finding evidence (rule ID, impact, help text, selector, snippet). Never full page source, credentials or approval tokens.
- Logging without keys, tokens, full URLs with query strings or page content.
- Tests for success and failure using a fake model client: success, bad JSON, unknown tool, schema violation, timeout, 429 then success, 429 then failure, 5xx, budget exceeded, no key.

RULES:
- Check the provider's current documentation for the base URL, header names and model names. Do not guess them. Mark anything you cannot confirm as TODO(verify) and tell me.
- Never expose the key client-side or hardcode it.
- The model must never apply a change, write a diff, or set a status. Do not add tools that can.
- Do not add unrelated functionality or new endpoints.

OUTPUT:
Implement and verify the integration. Report the configuration, the environment variables required, files changed, tests performed with results, and remaining limitations.
```

### 1b. Template for any other service

```
You are a senior integration engineer experienced in building reliable production integrations.

CONTEXT:
Follow docs/API.md, docs/architecture.md and AGENTS.md. Check docs/PRD.md first: this integration must be a named requirement in the current tier. If it is not, stop and ask.

TASK:
Integrate this external service:
[SERVICE / API NAME + PURPOSE]

Implement:
- Secure authentication and configuration from environment variables
- Only the API operations this requirement needs
- Request and response handling with schema validation of input and output
- Timeouts, and error handling that maps to the error codes in docs/API.md
- Rate-limit handling where relevant
- Retries only where safe (never for writes)
- Webhooks and signature verification only if the provider requires them (the project has none today, so ask first)
- Logging without exposing sensitive data
- Tests for success and failure cases, using a fake client, with no network

RULES:
Never expose API keys client-side or hardcode secrets. Follow the provider's documented behaviour and confirm it from the documentation. Make failures graceful, and prevent duplicate operations where relevant. Update docs/API.md in the same change. Do not add unrelated functionality.

OUTPUT:
Implement and verify the integration. Report the configuration, the environment variables required, files changed, tests performed and any remaining limitations.
```

---

## 2. Testing and QA

```
You are a senior QA engineer and test automation specialist responsible for software quality.

CONTEXT:
Read docs/PRD.md, docs/API.md, docs/architecture.md, docs/design.md and the current implementation before testing. Follow AGENTS.md.

TASK:
Create and run a practical test strategy for [FEATURE OR TIER, for example "Tier 1 core loop"].

Test:
- The core loop: scan, explain, agent drafts, approve, apply to copy, re-test, status
- Happy paths for each template T1 to T5 on the Golden Site
- Edge cases: template target missing or matching more than once, page with no findings, page that fails to load, very long snippets, more findings than the limit
- Invalid inputs: bad URL, wrong scheme, missing consent, blocked ranges (private, link-local, metadata, IPv6), redirects into blocked ranges, oversize or control-character wording edits
- Authorisation on the server: apply without a token, with a reused token, with an expired token, with a token for an edited diff, apply to a scan that is not the bundled demo, path escape attempts
- Verifier outcomes: passed, partial, failed (bad patch), failed (introduced finding), failed (control page regression), needs a person
- Failure paths: no AI key, provider error, malformed model output, timeout, budget exceeded (each must fall back and say why), Chromium unavailable, re-scan failing after a patch (snapshot restored)
- Original demo files hash-identical after any apply
- Export contains no token, key, or page source
- Loading, empty and error states in the UI, and the System log lines for each error code
- Keyboard-only operation, visible focus, contrast in light and dark themes, reduced motion
- UI strings contain none of the banned words (compliant, certified, conformant, fully accessible, any score or percentage)
- Responsive layout at narrow widths
- No leftover browser processes after 20 scans

Add unit tests for pure logic (templates, contrast, matching, status), integration tests for the API, and a small number of end-to-end tests that run the core loop in a browser. Run the self-audit on our own UI once it exists.

RULES:
Prioritise the core loop and the trust rules over superficial coverage. Tests must not need the network or a real AI key. Do not modify production behaviour just to make tests pass. Investigate failures rather than masking them. Do not delete, skip or loosen tests.

OUTPUT:
Report tests created and run, passed and failed cases, bugs found with severity (blocker, high, medium, low), and recommended fixes. State clearly anything you could not run.
```

---

## 3. Debugging and root cause

```
You are a senior debugging engineer responsible for diagnosing software issues.

CONTEXT:
Follow the project's existing architecture and code, the documents in docs/, and AGENTS.md.

PROBLEM:
[ERROR / BUG / LOG / SCREENSHOT]
What I expected: [EXPECTED]
What happened: [ACTUAL]
Steps to reproduce: [STEPS]
Environment: [OS, Python and Node versions, browser, with or without an AI key]

TASK:
Investigate systematically.
1. Reproduce or trace the failure.
2. Inspect the relevant code, logs, data and dependencies.
3. Identify the actual root cause.
4. Explain why it happens.
5. Implement the smallest correct fix.
6. Write a test that fails before the fix and passes after it.
7. Run the related tests and check for regressions.

Known traps in this project to rule in or out first:
- Playwright with Uvicorn on Windows raising NotImplementedError (the --reload event-loop problem)
- Axe selector not matching the source element, so a template found zero or several targets
- The control page not sharing the stylesheet, so the regression check proves nothing
- An axe "incomplete" result being treated as a failure
- A model output being parsed to decide a status
- The browser not closed after an error
- A stale or reused approval token

RULES:
Do not guess or randomly patch code. Do not hide errors, weaken validation, remove tests, or change unrelated behaviour. Preserve existing behaviour unless the bug requires otherwise. Do not break a trust rule in AGENTS.md section 1. If the evidence is not enough, say exactly what is missing and what you need.

OUTPUT:
Report the root cause, the fix, files changed, tests performed and any remaining risk.
```

---

## 4. Deployment and production setup

AccessPilot is a local, single-user tool. Per `docs/PRD.md`, a hosted version is out of scope: it would need authentication, roles and per-user scan ownership. For the hackathon, "deployment" means making the project run reliably on the demo machine. Use 4a for that. Use 4b only if the team decides to host it, and expect to add authentication first.

### 4a. Demo machine readiness (use this one)

```
You are a senior DevOps engineer experienced in preparing reliable software for live demos.

CONTEXT:
Follow docs/architecture.md, docs/API.md (section 14) and AGENTS.md. The product is local and single-user. The backend binds to 127.0.0.1 on port 8000.

TASK:
Prepare the project to run on the demo machine and verify it end to end.

Configure and verify:
- A clean setup from README.md on a second machine, timed (target 15 minutes)
- Python virtual environment, pinned dependencies, and `python -m playwright install chromium`
- Frontend production build and a start script for the backend and frontend (start.ps1 and start.sh)
- The backend started without --reload (or with the event-loop policy set deliberately) and tested on Windows
- .env.example complete, a real .env not committed, and the app starting in built-in mode with no AI key
- With an AI key: a successful model-backed run, and a clean fallback when the key is removed
- Core loop run three times in a row with the network off
- Health check at /api/health showing browserAvailable, modelConfigured and engineVersion
- No leftover Chromium processes after 20 scans
- CORS limited to the configured frontend origin
- Temporary working copies created and removed correctly
- A screen recording of one clean run as a backup

RULES:
Never commit secrets or put real keys in scripts. Do not delete existing data or files outside the project's temporary folders. Verify the production build before calling it ready. Flag anything that needs manual approval or a person to decide.

OUTPUT:
Prepare and verify the setup. Report the configuration, the environment variables required, the commands to start everything, results of each check above, and any remaining manual steps.
```

### 4b. Hosted deployment (only if the team decides to host)

```
You are a senior DevOps engineer experienced in deploying secure production applications.

CONTEXT:
Follow docs/architecture.md, docs/API.md and AGENTS.md. docs/PRD.md says hosting is out of scope. Before starting, list what hosting changes and what must be built first: authentication, roles, per-user scan ownership, rate limits per user, a safer sandbox for scanning arbitrary URLs, and a decision on where working copies live. Stop and ask me to confirm.

TASK:
Prepare the application for production deployment.

Configure and verify:
- Production build of the frontend and the backend
- Hosting environment that can run Chromium (memory, sandbox flags and dependencies)
- Environment variables and secrets held in the host's secret store
- Storage decisions (the product is in memory today, so say what must persist, if anything)
- Domain and HTTPS
- CORS limited to the production frontend origin
- Build and start commands
- Health checks and error handling
- The model provider configured, with a working fallback
- Logging that never records secrets, tokens, page source or full URLs with query strings

RULES:
Never commit secrets or use development credentials in production. Do not destroy existing data. Verify the production build before deployment. Follow the deployment strategy in docs/architecture.md, and flag anything requiring manual approval.

OUTPUT:
Prepare the deployment, verify it, and report the configuration, environment variables required, deployment status and any remaining manual steps.
```
