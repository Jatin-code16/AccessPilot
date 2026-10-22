# AccessPilot: Product Requirements Document

**Version:** 4.0
**Status:** Source of truth for what we build. If another file disagrees with this one, this file wins, except for UI details, where `design.md` wins.
**Event:** Microsoft Agentic AI Hackathon, Rungta International Skills University, Bhilai. 22 October 2026, 9:00 to 17:00.
**Problem statement chosen:** Automated Accessibility Checker (check websites against WCAG, use Copilot for analysis and suggestions).
**Team size:** 2 to 4.

**Product principle:** evidence first, AI draft second, human approval before any change, and a deterministic re-test decides whether a fix worked.

Priority legend:

- **P0** required for the demo. Build first, in the order given in section 7.
- **P1** build only after every P0 item passes its acceptance test.
- **P2** stretch. Build only if P0 and P1 are stable and time remains.
- **Later** not in this hackathon. Shown on the roadmap slide only.

---

## 1. Summary

AccessPilot scans a web page for accessibility problems in a real browser, shows each problem in plain language, has an AI agent draft a small fix, waits for a person to approve the exact change, applies it to a copy of the page, and re-scans to show what actually changed. It also says plainly what it did not test.

The interface is a live page on the left and a plain log on the right. Nothing happens that is not written in the log first (see `design.md`).

## 2. Problem

Accessibility scanners produce long lists of technical violations. They rarely help a developer to:

1. understand which person is blocked and from doing what,
2. pick a small, safe fix,
3. confirm the fix worked and broke nothing else,
4. know what the scanner did not test.

AI can explain issues and draft fixes, but it can invent rules or produce patches that cause regressions. Published research on LLM repair reports failure modes such as irrelevant edits and missed instances of a problem. Teams end up either ignoring AI output or trusting it too much. Overlay products that promised automatic compliance have drawn regulator action, so overclaiming is a real risk for any tool in this space.

**Example story used in the demo:** a college scholarship form that a keyboard-only or screen-reader user cannot complete. The barriers are an unlabelled email field, an image with no alternative text, low-contrast helper text, a page with no `lang`, and an icon-only button with no name.

## 3. Value proposition

> Scanners tell you what is wrong. AccessPilot shows what it checked, lets an agent draft a small change you approve, and proves by re-testing whether the change helped. It also tells you what it could not test.

What makes it different from a scanner or a chat assistant:

| # | Difference | Why it matters |
|---|-----------|----------------|
| A | **Visible work.** Every step is a log line with the actor and a real duration. | Nobody has to trust a black box. |
| B | **Verified repair.** Approved patch goes to a copy, then the same checks run again, plus a regression check. | "Fixed" means observed, not claimed. |
| C | **Honest limits.** What ran, what did not, what needs a person. No score. | Avoids false confidence. |
| D | **AI with boundaries.** The agent reads evidence and drafts. It cannot apply a change or set a result. | Agent help without losing trust. |
| E | **Works offline and without an AI key.** Built-in guidance is the fallback. | A live demo that does not depend on venue Wi-Fi. |

## 4. Users

| Persona | Need | Main use |
|---------|------|----------|
| Frontend developer | A short issue list and small, reviewable fixes | Scan, review, approve a fix |
| Site maintainer (college or government) | Plain-language guidance and a shareable report | Scan, read, export |
| QA or accessibility auditor | Repeatable findings and a list of what still needs human judgement | Scan, read coverage, export |
| Disabled end user (indirect) | To be able to apply, pay, book or study | Benefits from the fixes |
| Hackathon judge | Real Copilot usage, and a clear line between AI advice and evidence | Watches the demo, reads the log |

## 5. The core loop

```
Scan  ->  Explain  ->  Agent drafts fix  ->  Human approves  ->  Apply to copy  ->  Re-test proves it
```

If this loop works end to end on the Golden Site, three times in a row, the demo is complete. Everything else is optional.

## 6. User journeys

### J1. Scan and understand (P0)
1. The user enters a URL (or picks the bundled Golden Site) and confirms they are authorised to test it.
2. AccessPilot loads the page in a real browser and runs the rule engine.
3. Boxes appear on the page. The log shows what was loaded, what was checked, and how many issues were found, grouped by impact.
4. Each issue has a one-sentence explanation of who is blocked and from doing what.

### J2. Agent drafts a fix (P0)
1. The user presses **Run agent**.
2. The agent reads the findings through tools and drafts a fix for each finding that has a supported template. Every tool call appears in the log.
3. For findings with no template, the agent marks them "Needs a person" with a reason.
4. If no model is configured or the model fails, built-in guidance is used and the log says why.

### J3. Approve, apply, verify (P0, bundled demo only)
1. The log pauses at a "Your turn" card with the exact diff, the risk, and the impact line.
2. The user chooses **Approve**, **Edit wording** (for alt text or label text only) or **Skip**.
3. On approval, the patch is applied to a fresh copy of the demo site. The original files are never changed.
4. The same scan runs again on the copy, and the control page is scanned as a regression check.
5. A Result card shows one status (Passed, Partly passed, Failed, Needs a person) with resolved, remaining and new counts.
6. The user continues with the next finding on the patched copy.

### J4. Export (P1)
The user downloads a JSON report: scope, evidence, labelled AI drafts, decisions, results and limits. No secrets, no tokens, no full page source.

### J5. Keyboard walk (P1)
The scan also presses Tab up to 30 times, records the focus path, flags repeated focus (a loop) and clickable elements that never received focus. The path is drawn on the page and summarised in the log.

## 7. Scope by tier and build order

Build in this order. Finish each tier, including its tests, before starting the next.

### Tier 1 (P0): the core loop

| Order | Item | Done when |
|-------|------|-----------|
| 1 | Repo, FastAPI and Vite skeletons, Playwright with Chromium, axe-core vendored locally | `/api/health` answers and the frontend loads |
| 2 | Golden Site (5 seeded defects) and the control page | You can open both and see the Golden Site is broken |
| 3 | Scan service and `POST /api/scans` | The seeded defects come back as JSON |
| 4 | Plain-language explanations and the log UI | A person can read each issue without raw JSON |
| 5 | Templates T1 to T5 and the built-in (fallback) agent | Each template produces the right diff on the Golden Site |
| 6 | Approval, working copy, apply | Approve changes only the copy |
| 7 | Verifier and Result card | Status comes from the re-scan |

Exit test for Tier 1: the whole loop runs three times in a row without errors, with the network off and no AI key.

### Tier 2 (P1): credibility

1. Real model through the agent loop, with budgets and the fallback kept intact
2. Live log streaming (server-sent events)
3. Keyboard walk and the path on the page
4. Coverage view ("Ran", "Did not run", "Needs a person")
5. Boxes drawn on the page during the scan
6. JSON export
7. Self-audit script for AccessPilot's own UI

### Tier 3 (P2): stretch, in this order

1. India statute lookup: a fixed table from rule to citation, shown inside "Show" as a reference only
2. An approximate screen-reader line before and after a fix, with a text version and optional speech
3. Rollback to the previous working-copy snapshot
4. Before and after element crops
5. VS Code extension (diagnostics and quick fixes for the same templates)

### Later (roadmap slide only)

Multi-agent specialist team, full IDE workbench shell, demographic impact dashboard, nine-page site, GitHub pull request creation, CI gates, authenticated scans, hosted multi-user version.

## 8. Functional requirements

Acceptance criteria are written so they can be turned into automated tests.

### 8.1 Tier 1 (P0)

| ID | Requirement | Acceptance criterion |
|----|-------------|----------------------|
| FR-01 | Accept an `http` or `https` URL plus an explicit authorisation flag | Missing flag returns `consent_required`. Other schemes return `invalid_url`. |
| FR-02 | Block private, link-local, reserved and cloud-metadata targets. Allow loopback only as a development exception. | Unit tests for each blocked range. The browser also refuses redirects into blocked ranges. |
| FR-03 | Run axe-core in Playwright Chromium with WCAG A and AA tags (2.0, 2.1, 2.2) plus best-practice tags | The Golden Site returns the seeded findings for D01 to D05. |
| FR-04 | Normalise violations and incomplete results into one `Finding` shape and count passes | Response matches the types in `architecture.md`. |
| FR-05 | Attach a plain-language explanation to each finding from a fixed knowledge table | Each seeded rule has `who`, `blockedFrom` and `why`. No model needed. |
| FR-06 | Built-in agent: for every finding, produce an explanation and, where a template exists, a proposal | Works with no key, a provider outage, bad output or a budget overrun. |
| FR-07 | Repair templates T1 to T5 (section 9) with a path allowlist | Unsupported finding returns `needs_human`. Disallowed path returns `path_not_allowed`. Missing target returns `template_mismatch`. |
| FR-08 | Proposals carry a unified diff generated by code, never by the model | Diff hash is stable for the same inputs. |
| FR-09 | Editing wording (alt text, label text) regenerates the diff | Old approval token is void after an edit. |
| FR-10 | Approval creates a single-use token tied to the proposal ID and diff hash | Apply without a valid token returns `approval_required`. Reused token is refused. |
| FR-11 | Apply only to an isolated working copy. Never patch the original. | A test hashes the original files before and after any apply and finds no change. |
| FR-12 | Save a snapshot of the working copy before each apply | Snapshot exists before the file changes. |
| FR-13 | Re-scan the working copy, compare findings by match key, derive a status | Bad patch gives Failed. Good patch gives Passed. Partial fix gives Partly passed. |
| FR-14 | Regression check: scan the control page in the same working copy and compare to its baseline | A patch that adds a new finding on the control page gives Failed. |
| FR-15 | Trace: every step records actor, name, input summary, output summary, duration, ok | Trace entries match executed steps one to one. |
| FR-16 | Log UI per `design.md`: one line per trace entry, actor tags, durations, "Show" detail | No invented lines. |
| FR-17 | "Your turn", "Needs a person" and "Result" cards per `design.md` | Needs-a-person cards have no Approve button. |
| FR-18 | Status words come only from the verifier | The model output is never read when setting a status (code review item and a test). |

### 8.2 Tier 2 (P1)

| ID | Requirement | Acceptance criterion |
|----|-------------|----------------------|
| FR-20 | Agent loop with a real model and bounded tools: `list_findings`, `get_evidence`, `list_templates`, `draft_repair`, `mark_needs_human`, `submit_report` | Max 8 turns, 14 tool calls, 90 s per run, 20 s per model call. On any limit, fall back and log why. |
| FR-21 | Stream trace entries to the UI with server-sent events | Streamed entries equal the final trace. |
| FR-22 | Keyboard walk, up to 30 stops or 5 s, with repeated-focus detection and a clickable-but-not-focusable heuristic | The Golden Site shows the focus loop and flags the clickable `div`. |
| FR-23 | Coverage view: engine and version, tags, counts, "Did not run" list, "Needs a person" list | Present in the UI and in the export. No score. |
| FR-24 | Page overlay boxes, synced with the log | Clicking a box opens its card. The overlay is `aria-hidden`. |
| FR-25 | JSON export | No tokens, keys or full page source (automated test). |
| FR-26 | Self-audit script for AccessPilot's own UI | Zero serious or critical findings in light and dark themes. |

### 8.3 Tier 3 (P2)

| ID | Requirement | Acceptance criterion |
|----|-------------|----------------------|
| FR-30 | India statute lookup (RPwD Act 2016, GIGW 3.0, IS 17802) | Table filled and checked by a person from the official texts. Shown only inside "Show" with "Reference only. Not a compliance claim." |
| FR-31 | Approximate screen-reader line before and after a fix | Built from the accessibility tree. Labelled "Approximate". Text always visible. |
| FR-32 | Rollback endpoint restores the previous snapshot | Working copy equals the snapshot byte for byte. |
| FR-33 | Before and after element crops, in memory only | Crops are absent from the export. |
| FR-34 | VS Code extension | Diagnostics and quick fixes for T1 to T5, using the same backend. |

### 8.4 Process

| ID | Requirement | Acceptance criterion |
|----|-------------|----------------------|
| FR-40 | Real Copilot usage record in `docs/COPILOT_LOG.md` | Only real entries: prompt, what it produced, what we changed. |
| FR-41 | Frequent commits with clear messages, no squashing before judging | History shows the work. |

## 9. Golden Site and repair templates

### 9.1 Golden Site defects

| ID | Defect | Detected by | Repair | Tier |
|----|--------|-------------|--------|------|
| D01 | Email input with no label | axe `label` | T1 | 1 |
| D02 | Image with no `alt` | axe `image-alt` | T2 (human edits wording) | 1 |
| D03 | Low-contrast helper text | axe `color-contrast` | T3 | 1 |
| D04 | `<html>` with no `lang` | axe `html-has-lang` | T4 | 1 |
| D05 | Icon-only button with no name | axe `button-name` | T5 | 1 |
| D06 | Clickable `div` acting as a button | Keyboard heuristic | Needs a person | 2 |
| D07 | Focus cycle in a widget | Keyboard heuristic | Needs a person | 2 |
| D08 | No `main` landmark | axe `landmark-one-main` | Needs a person | 2 |
| D09 | Heading level skip | axe `heading-order` | Needs a person | 2 |
| D10 | "Click here" link text | Not found by the engine | Manual | 2 |

Every seeded element has a stable `id` so templates can find it. The control page is a clean page that shares the stylesheet with the Golden Site.

### 9.2 Templates

| T | Fix | Parameters | Edit rule |
|---|-----|-----------|-----------|
| T1 | Add `<label for="{id}">` before the input | `labelText` | Insert one label. If a label already exists, fail with `template_mismatch`. |
| T2 | Add an `alt` attribute to the image | `altText` | Set `alt` on the one matching `<img>`. Human can edit the wording. |
| T3 | Change the text colour in the stylesheet rule that applies to the element | `newColor` | Compute the contrast ratio against the background and choose the nearest passing colour. |
| T4 | Add `lang="en"` to `<html>` | `lang` | Edit the opening tag only. |
| T5 | Add `aria-label` to the button | `labelText` | Set the attribute on the one matching `<button>`. |

A template must find its target exactly once. Zero or several matches return `template_mismatch` and the finding becomes "Needs a person".

## 10. Non-functional requirements

| ID | Area | Target | How measured |
|----|------|--------|--------------|
| NFR-01 | Scan time, one local page | 30 s at the 90th percentile | `durationMs` over 10 runs |
| NFR-02 | Keyboard walk | 30 stops or 5 s, whichever comes first | Trace |
| NFR-03 | Browser cleanup | Browser closed in `finally`. No leftover processes after 20 scans. | Process count |
| NFR-04 | AI timeout | 20 s per call, 90 s per run, then fallback | Outage test |
| NFR-05 | Setup | 15 minutes from the README on a second machine | Stopwatch |
| NFR-06 | Export hygiene | No secrets, tokens or full page source | Automated test |
| NFR-07 | UI accessibility | Zero serious or critical findings on our own UI | Self-audit script and a keyboard-only pass |
| NFR-08 | Offline | Core loop works with the network off and no AI key | Airplane-mode rehearsal |
| NFR-09 | Platform | Windows first. Linux and macOS should work. | README commands |

## 11. Data

All data lives in memory for the life of the server process. Temporary working copies sit on disk and are deleted on exit. Full types are in `architecture.md`.

- **Scan:** id, URL, title, time, duration, status, engine and version, findings, incomplete items, pass count, keyboard walk, coverage, trace.
- **Finding:** match key, fingerprint, source, rule, impact, help text, tags, WCAG criteria, target selector, snippet (300 characters at most), explanation, template, needs-human flag.
- **Proposal:** id, scan, finding, template, status, rationale, files, risk, diff, diff hash, parameters, proposer, approval token.
- **Apply result:** status, reason, before and after scan IDs, comparison, control check, approver, time.
- **Agent run:** whether AI was used, model, fallback reason, explanations, proposals, needs-human list, trace.

The page source is never stored. Only bounded snippets are kept.

## 12. Integrations

| Integration | Purpose | Required |
|-------------|---------|----------|
| Playwright with Chromium | Real-browser scan and keyboard walk | Yes |
| axe-core, vendored (pin the exact version) | Rule engine, works offline | Yes |
| GitHub Models (OpenAI-compatible) | Default model for the agent | No. The fallback covers it. |
| Azure OpenAI | Alternative model provider | No |
| GitHub Copilot in VS Code | How we build (process, not runtime) | Yes, for the event |
| Web Speech API | Spoken line in the browser (P2) | No |

Model settings come from environment variables (`AI_PROVIDER`, `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL`). Nothing is hard-coded and nothing secret is committed.

## 13. Roles and permissions

The MVP is a local, single-user tool. There are no accounts or roles.

| Actor | Can | Cannot |
|-------|-----|--------|
| Local user | Scan, run the agent, approve, apply to the demo copy, export | Apply changes to any site other than the bundled demo. Bypass approval. |
| Agent (model) | Read evidence, draft proposals, flag items for a person, submit explanations | Apply changes, run commands, fetch URLs, write files, set any status |
| Verifier (code) | Decide the status from re-scans | Use model output |

## 14. Out of scope

Legal certification or compliance guarantees. Exhaustive WCAG coverage. Numeric accessibility scores. Overlays that inject fixes into third-party sites. Editing arbitrary or production sites. Crawling many pages. Authenticated targets. Accounts and hosted multi-user mode. GitHub pull requests. CI gates. SARIF or PDF reports. Driving real operating-system screen readers. Any claim that the focus list or the approximate speech line equals real screen reader output.

## 15. Wording rules for the product and the pitch

- Allowed status words: **Passed**, **Partly passed**, **Failed**, **Needs a person**. "Passed" means the automated re-test passed. It does not mean the page is accessible.
- Never write "compliant", "accessible" (as a verdict), "certified", "WCAG conformant", or any percentage of accessibility.
- AI output carries the word **Draft** until a person approves it.
- Statute citations are references only.
- In the pitch, quote only numbers we measured ourselves.

## 16. Success criteria

| Criterion | Target |
|-----------|--------|
| End-to-end demo | Scan, agent, approve, Passed, in about 3 minutes |
| Evidence | Every finding shows its rule ID and target (inside "Show") |
| Honest status | No result shown as Passed without a re-scan |
| Negative paths | Bad patch gives Failed. Regression gives Failed. Both covered by tests. |
| Offline | Works with the network off and no AI key |
| Reliability | Three clean rehearsals in a row |
| Self-audit | Zero serious or critical findings on our UI |
| Copilot | A real `COPILOT_LOG.md` and a readable commit history |

## 17. Demo script (about three minutes)

1. Open the Golden Site and press Scan. Boxes appear as log lines arrive.
2. The log shows five findings and the limits line.
3. Run the agent. Tool calls stream into the log. A "Your turn" card appears for the email label.
4. Press Approve. The log shows Apply, then Re-test.
5. The Result card shows Passed with the counts. Show the before and after lines if built.
6. Show a "Needs a person" card for the clickable `div` and say the tool will not guess.
7. Open Coverage and read the "Did not run" list aloud.
8. Close with: built with Copilot, and the product proves its own fixes.

Keep a screen recording of a clean run as a backup.

## 18. Risks

| Risk | Likelihood | Effect | Mitigation |
|------|-----------|--------|------------|
| Template edits do not match the real HTML | High | Core loop breaks | Test T1 to T5 against the Golden Site before any UI work |
| Axe selectors do not map to source elements | Medium | Wrong element patched | Stable `id` on every seeded element. Templates match by `id`. |
| No AI token or network at the venue | Medium | No live agent | Built-in agent is built first and is complete on its own |
| Chromium fails to launch on the demo machine | Medium | No scan | Install and test on the demo machine early. Keep a recording. |
| Scope growth | High | Half-finished demo | Tier order in section 7. Nothing from Tier 2 starts before Tier 1 passes. |
| Our UI fails its own audit | Medium | Credibility loss | Self-audit from the first UI commit |
| Overclaiming in the pitch | Medium | Credibility loss | Wording rules in section 15 |

## 19. Assumptions and decisions

| # | Item | Status |
|---|------|--------|
| 1 | Pre-event building is allowed | Confirmed by the organisers. Keep the message. Say it openly in the pitch. |
| 2 | Stack: FastAPI, Playwright (Python), React, Vite, TypeScript | Decided |
| 3 | Model through GitHub Models or Azure OpenAI | Decided. The fallback works without either. |
| 4 | Judges accept a local, not hosted, demo | Assumption |
| 5 | A token with GitHub Models access is available on the day | Assumption. Otherwise we demonstrate the fallback. |
| 6 | Which Copilot product the organisers expect (Copilot in VS Code or Microsoft 365 Copilot) | Open. Ask the organisers. |
| 7 | Whether to scan a real public page, read-only, in the demo | Open. Team decision. |
| 8 | Submission deadline | Open. Ask on arrival and finish early. |

## 20. Roadmap (for the last slide)

Multi-agent triage, VS Code extension with quick fixes, India statute and demographic impact view, pull request creation with evidence, CI gate, authenticated scans, and a hosted version with accounts.

## 21. Glossary

- **Finding:** one problem reported by the engine or the keyboard walk.
- **Match key:** rule ID plus target selector. Used to compare two scans.
- **Working copy:** a temporary copy of the demo site that patches are applied to.
- **Control page:** a clean page in the working copy, scanned after every apply to catch regressions.
- **Template:** a fixed, code-generated repair (T1 to T5).
- **Needs a person:** a finding the tool will not try to fix automatically.
