# AccessPilot: Project Context

Read this first. It explains what the project is, why it exists, how it is built, what was decided and why, and where everything lives. A person or an AI coding agent who reads only this file should understand the project well enough to start working, then follow the links to the detailed documents.

Keep this file current. See section 22.

---

## 1. One-paragraph summary

AccessPilot is a local tool that scans a web page for accessibility problems in a real browser, explains each problem in plain language, lets an AI agent draft a small fix, waits for a person to approve the exact change, applies it to a copy of the demo site, and re-scans to show what actually changed. It also states what it did not test. The interface is a live page on the left and a plain log on the right, and nothing happens that is not written in the log first.

## 2. Event and constraints

| Item | Detail |
|------|--------|
| Event | Microsoft Agentic AI Hackathon |
| Venue | Rungta International Skills University, Bhilai (in person) |
| Date and time | 22 October 2026, 9:00 to 17:00 |
| Team size | 2 to 4 |
| Problem statement | Automated Accessibility Checker: scan websites against WCAG, use Copilot for analysis and suggestions |
| Judging signals | Real Copilot usage, a working prototype, a clear demo |
| Only one team qualifies from Round 1 | The demo must be clear and reliable |
| Pre-event building | The organisers said it is allowed. Keep the message. Say so openly in the pitch. |
| Submission deadline | Not announced. Ask on arrival. |

Because the build time is short, the project is organised in tiers (section 7) and the core loop comes before everything else.

## 3. The problem

Accessibility scanners produce long lists of technical violations. They rarely tell a developer which person is blocked and from doing what, which small change is safe, whether the change worked, or what the scanner did not test. AI can draft explanations and fixes, but it can invent rules and write patches that break other things, so teams either ignore it or trust it too much.

Evidence we collected while researching (verify before quoting any number in the pitch):

- Automated coverage is debated. A Deque study of 2,000+ audits reports that 57% of issues by volume were fully covered by automation, while only 16 of 50 WCAG 2.1 AA criteria had automated findings. This is a vendor-run study.
- A UK government audit that seeded 142 barriers into a page found the best of 13 tools caught 40%.
- Lighthouse accessibility scores of 100 do not mean a page meets WCAG.
- The US FTC fined the overlay vendor accessiBe $1 million for unsubstantiated claims that its AI tool made sites WCAG-compliant. Overclaiming is a real risk for any tool in this space.
- Research on LLM repair (A11y-Bench) reports failure modes such as irrelevant edits and missed instances. AccessGuru classifies violations as syntactic, semantic and layout, and combines a rule engine with an LLM.
- Microsoft's Accessibility Insights combines automated checks with a guided keyboard check and highlights failures on the page. Deque's axe MCP Server gives coding agents analyze and remediate tools in the IDE (paid product).

What this means for us: scanning alone is not new, and "agent plus axe in an IDE" already exists. Our edge is a **visible log, human approval of the exact change, and a deterministic re-test**, with honest limits.

## 4. What the product does

The core loop:

```
Scan  ->  Explain  ->  Agent drafts fix  ->  Human approves  ->  Apply to copy  ->  Re-test proves it
```

Demo story: a college scholarship form that a keyboard-only or screen-reader user cannot complete. Five seeded problems (missing label, missing alt text, low contrast, no `lang`, icon-only button) can be repaired by templates. Others (clickable `div`, focus loop, no `main` landmark, heading skip) are shown as "Needs a person".

The three-minute demo: scan, run the agent, review the exact diff, approve, watch the re-test, see a Passed result with counts, then show a Needs a person card and the "Did not run" list.

## 5. Core principles

1. **Evidence first, AI second.** The scanner's output is evidence. The agent's output is a Draft.
2. **Human approval before any change.** The log pauses at a "Your turn" card.
3. **A deterministic re-test decides the result.** No model output ever sets a status.
4. **Honest limits.** No score, no percentage, no "compliant" claim. Say what did not run.
5. **Transparent by default.** Everything the system does is a log line with the actor and a real duration.
6. **Works offline and without an AI key.** The built-in agent is complete on its own.
7. **Our own UI must pass an accessibility audit.**

### Trust boundaries (never weaken)

| Rule | How it is enforced |
|------|--------------------|
| The model proposes, never applies | Agent tools are read-only except `draft_repair`, which returns a proposal object and writes nothing |
| The model never writes patches | It picks a template (T1 to T5) and fills parameters. Code generates the diff. |
| A human approves the exact change | Single-use token bound to proposal ID and diff hash |
| The original is never touched | Apply only inside a copied working directory, with a path allowlist |
| Status comes from evidence | Verifier compares findings from two scans |
| No compliance claims | Four fixed status words, no score anywhere |

## 6. Users

Frontend developers (review and approve fixes), site maintainers (plain-language guidance, report), accessibility auditors (repeatable findings, list of what needs a person), and hackathon judges (real Copilot use, clear line between AI advice and evidence). Disabled end users benefit indirectly.

The MVP is a local, single-user tool. There are no accounts or roles.

## 7. Scope and tiers

| Tier | Contents | Rule |
|------|----------|------|
| 1 (P0) | Golden Site, scan, plain-language explanations, log UI, templates T1 to T5, built-in agent, approval, working copy, apply, verifier, Result card | Build first. Exit test: whole loop runs three times in a row, network off, no AI key. |
| 2 (P1) | Model agent loop, live log streaming, keyboard walk, coverage view, overlay boxes, JSON export, self-audit | Only after Tier 1 passes |
| 3 (P2) | India statute lookup, approximate screen-reader line, rollback, before/after crops, VS Code extension | Stretch |
| Later | Multi-agent team, IDE shell, demographic dashboard, nine-page site, pull requests, CI gate, authenticated scans, hosting with accounts | Roadmap slide only |

Earlier drafts of the PRD marked nearly everything P0, including a multi-agent team, a speech simulator, an India compliance dashboard, a VS Code extension and a nine-page site. That was cut because it does not fit one day and it made the priorities meaningless.

## 8. How it is built

### Stack

| Area | Choice |
|------|--------|
| Backend | Python, FastAPI, Pydantic, pytest |
| Browser automation | Playwright for Python, Chromium |
| Rule engine | axe-core, vendored locally (pinned version), loaded from disk |
| Frontend | React, Vite, TypeScript (strict) |
| Model access | OpenAI-compatible client to GitHub Models or Azure OpenAI. Optional. |
| Storage | In memory only. Temporary working copies on disk. No database. |
| Platform | Windows first. Linux and macOS should work. |

### Parts

- **Scan service:** validates the URL, launches Chromium, runs axe, normalises findings, runs the keyboard walk (Tier 2), closes the browser in `finally`.
- **Agent service:** a built-in agent (deterministic, always available) and an optional model agent that uses bounded read-only tools. Limits: 8 turns, 14 tool calls, 90 seconds per run, 20 seconds per model call. Any limit or error falls back to the built-in agent and says why.
- **Repair engine:** templates T1 to T5 (pure functions returning new source and a unified diff), proposals, approval tokens, the working copy, snapshots, apply.
- **Verifier:** re-scans the patched copy, compares findings by match key (resolved, remaining, introduced), scans the control page for regressions, derives the status.
- **Frontend:** one screen with a page pane (iframe plus overlay) and a log pane with lines and cards.

### Data flow

1. The user enters a URL and confirms authorisation. `POST /api/scans` returns a `Scan` with findings and a trace.
2. The user runs the agent. `POST /api/scans/{id}/agent` returns explanations, proposals with diffs, and needs-a-person items.
3. The user approves one proposal. `POST /api/proposals/{id}/approve` returns a single-use token.
4. `POST /api/proposals/{id}/apply` with the token copies the demo site if needed, snapshots, patches, re-scans, scans the control page, and returns an `ApplyResult` with a status.
5. The UI renders every trace entry as a log line and shows the Result card.

### Status words

Backend values `passed`, `partial`, `failed`, `needs_human` appear in the UI as **Passed**, **Partly passed**, **Failed**, **Needs a person**. "Passed" means the automated re-test passed. It does not mean the page is accessible.

### Verification logic

- Match key is rule ID plus target selector. Snippets are not part of it because patches change snippets.
- Passed: target finding resolved, nothing introduced, control page clean.
- Partly passed: some targeted findings resolved, others remain, nothing introduced, control clean.
- Failed: target still present, or anything introduced, or the control page regressed.
- Needs a person: the finding has no template.
- The control page shares `shared.css` with the Golden Site and sits in the same working copy, so a bad stylesheet change can really break it.

### Repair templates

| T | Fix |
|---|-----|
| T1 | Add a `<label for>` to an input |
| T2 | Add `alt` to an image (wording editable by a person) |
| T3 | Change a text colour in the stylesheet to a passing contrast value (computed) |
| T4 | Add `lang="en"` to `<html>` |
| T5 | Add `aria-label` to an icon-only button |

A template must find its target exactly once, by stable `id`. Zero or several matches return `template_mismatch` and the finding becomes Needs a person.

## 9. The interface in brief ("Open Workbench")

Two panes. Left: the real page in an iframe with boxes drawn on what is checked. Right: a plain, ordered log. Each line is `[Actor] short sentence, real duration, Show`. Actors are told apart by a text tag and a border: Scanner (solid grey), Agent (dashed amber, "Draft"), You (solid blue), Re-test (green or red with a word), System (muted).

Three card types: **Your turn** (exact diff, impact line, Approve, Edit wording, Skip), **Needs a person** (no Approve button), **Result** (status word, resolved, remaining, new, control page). Flat style, no gradients, glow, emoji, chat bubbles or score rings. Light theme by default with a dark option. Full rules are in `design.md`.

## 10. Data and state

All data is in memory for the life of the server process. The page source is never stored, only snippets of 300 characters or fewer. Screenshots and crops, if built, stay in memory and are never exported. Types (`Finding`, `TraceEntry`, `Scan`, `Proposal`, `ApplyResult`, `AgentRun`) are defined in `architecture.md` section 4. There is no `DATABASE.md` because there is no database.

## 11. API in brief

`GET /api/health`, `POST /api/scans`, `GET /api/scans/{id}`, `POST /api/scans/{id}/agent`, `GET /api/scans/{id}/agent/stream`, `GET /api/proposals/{id}`, `PATCH /api/proposals/{id}`, `POST /api/proposals/{id}/approve`, `POST /api/proposals/{id}/skip`, `POST /api/proposals/{id}/apply`, `POST /api/workspaces/{id}/rollback`, `GET /api/scans/{id}/export`. One error shape. Details in `API.md`.

## 12. Golden Site

A small scholarship application form with ten seeded defects (D01 to D10, listed in `PRD.md` section 9). Every seeded element has a stable `id`. A control page, which is clean, shares the stylesheet. Both live in `sites/` and are copied into `work/{id}/` on the first approval.

## 13. External services

| Service | Use | Required |
|---------|-----|----------|
| Playwright and Chromium | Real-browser scan | Yes |
| axe-core (vendored) | Rule engine | Yes |
| GitHub Models or Azure OpenAI | Model for the agent | No |
| GitHub Copilot in VS Code | How we build | Yes, for the event |
| Web Speech API | Spoken line in the browser (Tier 3) | No |

No webhooks. No database. No accounts.

## 14. Decisions log

| Decision | Reason |
|----------|--------|
| Core loop first, extras later | One day of build time. Only one team advances. |
| Model chooses templates, code writes diffs | Research shows LLM patches can hallucinate or miss instances |
| No score, no "compliant" | Scores mislead. Overlay vendors were fined for overclaiming. |
| Two-pane log UI instead of an IDE shell or dashboard | Simpler, easier to make accessible, makes every action visible |
| Built-in agent built before the model agent | Demo must work with no key and no network |
| In-memory storage only | No persistence needed for a local demo |
| Status words changed from "Verified" to "Passed" | "Verified" overstates what an automated re-test shows |
| VS Code extension moved to stretch | Large effort, not needed for the core story |
| GitHub Models or Azure OpenAI, not other providers | Fits a Microsoft event |
| Control page in the same working copy | Otherwise the regression check proves nothing |

## 15. Document map and authority

| File | Purpose |
|------|---------|
| `CONTEXT.md` | This file. Overview and history. |
| `PRD.md` | What to build, in what order, and the acceptance criteria. Wins on scope and priority. |
| `architecture.md` | Structure, types, services, error codes. Wins on structure. |
| `API.md` | Endpoints, formats, integrations, limits, environment variables |
| `design.md` | Look, layout, wording, accessibility of the UI. Wins on anything visual. |
| `AGENTS.md` | Rules for any coding agent |
| `copilot-instructions.md` | Short Copilot-specific rules, placed at `.github/copilot-instructions.md` |
| `PROMPTS.md` | Task prompts for integration, testing, debugging and deployment |
| `COPILOT_LOG.md` | Real record of Copilot use. Real entries only. |

Order of authority when files disagree: PRD for scope, architecture for structure, API for endpoints, design for visuals. If a conflict is real, stop and ask. Do not choose silently.

## 16. Conventions

- JSON uses camelCase. Times are ISO 8601 in UTC. IDs are opaque strings.
- One error shape: `{ "error": { "code", "message" } }`, with codes only from the lists in `architecture.md` and `API.md`.
- Log lines are 8 words or fewer. Impact lines are one sentence under 15 words.
- Banned words in the UI and the pitch: compliant, certified, conformant, fully accessible, any accessibility percentage or score.
- AI text carries "Draft" until a person approves it.
- Real durations only. No fake progress.
- Commit often with clear messages. Do not squash history before judging.

## 17. Known traps

- Playwright with Uvicorn on Windows can fail with `NotImplementedError` when `--reload` is used. Test on the demo machine and start without `--reload`, or set the event-loop policy deliberately.
- Axe selectors describe the rendered DOM, not the source. Templates match by stable `id`.
- Axe "incomplete" results are not failures. They become Needs a person.
- Load axe from disk, never a CDN.
- Real third-party pages often block iframes. Use a screenshot for any read-only scan of a real page.
- Contrast can be undecidable on dynamic backgrounds. Treat as Needs a person.

## 18. Risks

Template edits not matching real HTML (test T1 to T5 before any UI), no AI token or network at the venue (built-in agent), Chromium not launching on the demo machine (install and test early, keep a recording), scope growth (tier order), our UI failing its own audit (self-audit from the first UI commit), overclaiming in the pitch (wording rules).

## 19. Open questions

1. Which Copilot product do the organisers expect: Copilot in VS Code or Microsoft 365 Copilot? Ask them.
2. Will we show a read-only scan of a real public page, and which one?
3. Will a GitHub token with Models access be available on the day?
4. What is the submission deadline?
5. Who fills the India statute table from the official texts (Tier 3)?

## 20. Status

Update this table as work happens.

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| Repo and skeletons | TODO | | |
| Golden Site and control page | TODO | | |
| Scan service | TODO | | |
| Explanations and log UI | TODO | | |
| Templates and built-in agent | TODO | | |
| Approval, working copy, apply | TODO | | |
| Verifier and Result card | TODO | | |
| Tier 2 items | TODO | | |
| Copilot log kept | TODO | | |
| Three clean rehearsals | TODO | | |
| Backup recording | TODO | | |

## 21. How to run

Exact commands live in `README.md` and must be tested on a second machine. The usual steps: create a virtual environment, install `requirements.txt`, run `python -m playwright install chromium`, run `npm install` in `frontend`, copy `.env.example` to `.env`, then use the start script. The backend listens on port 8000 on the local machine only.

## 22. Keeping this file current

Update this file when a decision changes, a tier completes, a document is added, or an open question is answered. If code and this file disagree, fix whichever is wrong in the same change. Do not leave stale statements.

## 23. Glossary

- **Finding:** one problem reported by the engine or the keyboard walk.
- **Match key:** rule ID plus target selector, used to compare two scans.
- **Working copy:** a temporary copy of the demo site that patches are applied to.
- **Control page:** a clean page in the working copy, scanned after each apply to catch regressions.
- **Template:** a fixed, code-generated repair (T1 to T5).
- **Needs a person:** a finding the tool will not try to fix automatically.
- **Trace:** the ordered list of real steps with durations. The log renders it.
- **Built-in agent:** the deterministic agent that works without a model.
