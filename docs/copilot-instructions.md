# Copilot instructions for AccessPilot

Place this file at `.github/copilot-instructions.md` in the repository so Copilot reads it automatically. You can also paste sections of it into a chat when a task drifts.

You are helping build **AccessPilot**, a local tool that scans a web page for accessibility problems, shows them in a plain log, lets an AI agent draft small fixes, waits for a person to approve the exact change, applies it to a copy of the demo site, and re-scans to prove what changed. It is being built for a one-day hackathon, so the core loop matters more than extra features.

Read these before you change anything:

1. `docs/PRD.md`: what to build, in what order, and what counts as done.
2. `docs/architecture.md`: how the system fits together, the data types, the API, the error codes.
3. `docs/design.md`: how the interface must look and behave.

If these files disagree, the order of authority is: PRD for scope and priority, architecture for structure and types, design for anything visual.

---

## 1. Rules that never change

If a request would break one of these, do not do it. Say which rule it breaks and suggest an alternative.

1. **The model never applies a change.** Only code, after a person approves, writes to the working copy.
2. **The model never writes a patch or a diff.** Diffs come from the template functions in `repair/templates.py`.
3. **The model never sets a status.** Status comes from `verify/status.py` using two scans. No model text is read when deciding it.
4. **The original demo files are never modified.** Only files inside `work/{id}/` may be written.
5. **No numeric accessibility score, percentage or rating, anywhere.**
6. **Never write or display "compliant", "certified", "conformant", "fully accessible", or any claim that a page meets a standard.** The only status words are Passed, Partly passed, Failed, Needs a person.
7. **AI output is always labelled Draft** until a person approves it.
8. **Everything the system does appears in the log with a real duration.** Do not invent log lines, fake progress, or placeholder timings.
9. **Approval is single-use and tied to one diff hash.** Never reuse or bypass a token.
10. **The core loop must work with the network off and no AI key.** The built-in agent is complete without a model.
11. **No secrets in code, logs, exports or commits.** Keys come from environment variables only.
12. **Do not add features outside the current tier** (see section 4).

## 2. How to avoid making things up

Most mistakes in this project come from guessing. Follow these habits.

- **Do not invent package names, functions, parameters, endpoints, model names or environment variables.** If you are not sure something exists, check it: look at the installed package (`pip show`, `python -c "import x; help(x)"`, `npm ls`), read its type definitions, or read the file in this repository. If you still cannot confirm, leave a `TODO(verify): ...` comment and tell the user. Do not guess.
- **Do not invent axe-core rule IDs.** Use only rule IDs that the engine returns. The seeded ones are `label`, `image-alt`, `color-contrast`, `html-has-lang`, `button-name`, `landmark-one-main` and `heading-order`. If you need another one, run the scan and read the output.
- **Do not invent legal or standards citations.** `knowledge/statutes.py` is filled by a person from the official texts. Never generate section numbers for the RPwD Act, GIGW 3.0, IS 17802 or WCAG success criteria from memory. WCAG criteria in findings come from the engine's tags only.
- **Do not invent API endpoints or error codes.** The complete lists are in `architecture.md`. If you need a new one, propose it first and update the document in the same change.
- **Do not invent the GitHub Models or Azure OpenAI base URL or model names.** Read them from environment variables. Point the user to the provider's current documentation.
- **Do not make up numbers.** No made-up scan times, percentages, test counts or coverage claims in code, comments, docs or the UI. Use measured values only.
- **Do not claim a test passed unless you ran it.** If you could not run something, say so.
- **Pin versions.** When you add a dependency, add it to `requirements.txt` or `package.json` with an exact version that is already installed. Do not add a dependency without saying why.
- **Match the existing types.** Backend models and frontend types must follow `architecture.md` section 4 exactly, including field names and enum values.
- **Do not change a file you were not asked to change.** If a fix needs a change elsewhere, say so and ask.

## 3. Stack and conventions

| Area | Choice |
|------|--------|
| Backend | Python, FastAPI, Pydantic models, pytest |
| Browser automation | Playwright for Python with Chromium |
| Rule engine | axe-core, vendored in `backend/vendor/axe.min.js`, loaded from disk |
| Frontend | React, Vite, TypeScript (strict mode) |
| Model access | OpenAI-compatible client, configured by environment variables, optional |
| Storage | In memory only. Temporary working copies on disk |

Backend:

- Type-hint every function. Pydantic models for every request and response.
- One error shape: `{ "error": { "code", "message" } }`, using only codes from `architecture.md`.
- Close the browser in a `finally` block, every time.
- Templates are pure functions: no file or network access inside them.
- Keep functions short and named for what they do. No clever one-liners.
- Never print or log API keys, tokens, or full page source.

Frontend:

- TypeScript strict. No `any` unless a comment explains why.
- No `localStorage` or `sessionStorage`.
- Colours and spacing come from the tokens in `styles/tokens.css`. Do not hard-code hex values in components.
- Use real elements: `<button>`, `<a>`, `<ol>`, `<section>`, `<details>` or a disclosure button. No clickable `div`s. (This product checks for exactly that mistake.)
- Follow `design.md` for look, wording and states. Short sentences. No emoji, gradients, glow, shadows or chat bubbles.

Accessibility of our own UI is a requirement, not a polish step:

- Visible focus on every control, at least 44px targets, text contrast 4.5:1, real headings and landmarks, a live region for the log, and no colour-only meaning.

## 4. Scope control

Work in tiers. Do not start a tier until the one before it passes its exit test (`PRD.md` section 7).

**Tier 1 (build now):** Golden Site, scan, plain-language explanations, log UI, templates T1 to T5, built-in agent, approval, working copy, apply, verifier, Result card.

**Tier 2 (only after Tier 1 passes three clean runs):** model agent loop, SSE streaming, keyboard walk, coverage view, overlay boxes, JSON export, self-audit.

**Tier 3 (stretch):** statute lookup, approximate screen-reader line, rollback, before/after crops, VS Code extension.

**Not in this project:** multi-agent teams, an IDE-style shell, dashboards, a multi-page site, accounts, hosting, crawling, authenticated scans, pull request creation.

If the user asks for something outside the current tier, say which tier it belongs to and ask whether to proceed. Do not quietly add it.

## 5. How to work on a task

1. **Restate the task in one or two lines** and name the files you will touch. If anything is unclear, ask one specific question before writing code.
2. **Check the documents.** Find the relevant requirement ID (for example FR-07) and the relevant section of `architecture.md`. Say which one you are implementing.
3. **Make the smallest change that satisfies it.** One concern per change. No drive-by refactors.
4. **Write or update the test in the same change.** The acceptance criterion in `PRD.md` is the test.
5. **Run the tests and report the result honestly.** If you cannot run them, say that.
6. **Describe what changed**: files touched, what to run to check it, and anything left unfinished or uncertain.

Keep each change small enough to read in a few minutes. Commit after each working step.

## 6. Stop and ask first

Stop and ask the user before doing any of these:

- Changing a trust rule in section 1, a status value, an error code, or a data type.
- Adding a dependency, a new endpoint, or a new file outside the layout in `architecture.md`.
- Deleting or rewriting a working module.
- Anything that touches `sites/golden` in a way that changes which defects exist.
- Anything involving real credentials, tokens or the user's accounts.
- Anything that sends page content to an external service other than the configured model.
- A requirement that seems impossible or contradicts another one. Say so. Do not pick silently.

## 7. Known traps in this project

- **Templates must find their target exactly once**, by `id`. Zero or multiple matches raise `template_mismatch`. Do not fall back to a fuzzy match.
- **Axe selectors are not source locations.** Do not try to patch by selector text. Use the stable `id`.
- **Match key is `ruleId + "|" + target selector`.** Do not include the snippet, because patches change snippets.
- **The control page must share `shared.css` with the Golden Site and live in the same working copy**, otherwise the regression check proves nothing.
- **Playwright with Uvicorn on Windows** can fail with `NotImplementedError` when `--reload` is used. Do not "fix" it by changing unrelated code. Start without `--reload` or set the event-loop policy deliberately, and say what you did.
- **Axe "incomplete" results are not failures.** They become Needs a person items, never Failed.
- **The overlay on the page pane is `aria-hidden`.** The log carries the same information as text.
- **Do not read model output to decide a status.** If you find yourself parsing model text to set `passed` or `failed`, stop.
- **The built-in agent must keep working** whenever you change the model agent. Run the no-key test after every agent change.

## 8. Wording

When you write any text a user will read (UI, errors, log lines, README):

- Log lines are 8 words or fewer. Impact lines are one sentence under 15 words, naming the person and the blocked action.
- Plain words. "Label", not "accessible name". "Keyboard user", not "non-pointer user".
- Sentence case. No exclamation marks. No marketing language.
- Do not write "Fixed everywhere", "Accessible", "Compliant" or "AI-powered".
- Statute references only appear under "Show", with the line "Reference only. Not a compliance claim."

## 9. Tests that must exist

Each of these maps to an acceptance criterion in `PRD.md`. Do not mark a requirement done without its test.

- URL policy blocks private, link-local, metadata and reserved ranges
- Golden Site scan returns the seeded rule IDs
- Each template: exact diff, same output twice, `template_mismatch` on zero or multiple targets
- Contrast function returns known ratios, and T3 reaches 4.5
- Approval token: single use, voided by an edit, rejected on a wrong diff hash
- Original demo files are hash-identical after any apply
- Path escape attempts return `path_not_allowed`
- Verifier fixtures: passed, partial, failed (bad patch), failed (introduced), failed (control regression)
- Agent falls back on no key, bad output, timeout and budget overrun, and its tools cannot write files
- Export contains no token, key or page source
- UI strings contain none of the banned words
- Self-audit reports zero serious or critical findings (Tier 2)

## 10. Commits and the Copilot log

- Commit often, with messages that say what changed and why ("Add T1 label template with tests"). Do not squash history before judging.
- The team keeps `docs/COPILOT_LOG.md` with real entries only: the prompt used, what Copilot produced, and what the team changed or rejected. Do not write entries for things that did not happen. If asked to add an entry, write only what the user tells you.

## 11. Definition of done for a change

A change is done only when all of these are true:

- [ ] It implements a named requirement (FR-xx) from the PRD.
- [ ] It follows the types, endpoints and error codes in `architecture.md`.
- [ ] None of the rules in section 1 are broken.
- [ ] Its test exists and was run, and the result is reported.
- [ ] No invented names, numbers, citations or endpoints.
- [ ] UI changes follow `design.md`, with visible focus, contrast, keyboard access and no banned words.
- [ ] No secrets, no unrelated edits, no new dependency without a stated reason.
- [ ] You listed anything left unfinished or uncertain.

## 12. Reply format

Keep replies short and concrete:

1. **Task:** one line.
2. **Requirement:** the FR ID and the architecture section.
3. **Files changed:** a short list.
4. **How to check:** the exact command or steps.
5. **Test result:** what ran and what happened.
6. **Open items:** anything uncertain, skipped or needing a decision.

## 13. Prompts the team can paste

Use these to pull a drifting session back.

**Reset to the documents**
> Re-read docs/PRD.md, docs/architecture.md and docs/design.md. Tell me which requirement this task implements, which tier it belongs to, and which files you will change. Do not write code yet.

**Check for guessing**
> List every package, function, endpoint, rule ID and environment variable you used in this change. For each one, tell me how you confirmed it exists. Mark anything you could not confirm.

**Check the trust rules**
> Review this change against section 1 of copilot-instructions.md. For each rule, say whether it is affected and show the code that keeps it true.

**Check scope**
> Does this change belong to the current tier? List anything in it that is not required by a numbered requirement and remove it.

**Before a commit**
> Run the tests for the files changed. Report what ran and the result. Then check the definition of done in section 11 and list anything unmet.

**When stuck**
> Stop writing code. Explain what you are unsure about, what you tried, and what you need from me to continue. Do not guess.
