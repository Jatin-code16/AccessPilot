# AGENTS.md

Rules for any coding agent working on AccessPilot. Follow them for every task, however small. Place this file at the repository root.

AccessPilot is a local tool that scans a web page for accessibility problems, lets an AI agent draft small fixes, waits for a person to approve the exact change, applies it to a copy of the demo site, and re-tests to show what changed. The overview is in `docs/CONTEXT.md`.

---

## 0. Before you do anything

This root `AGENTS.md` is the always-on workspace instruction file. Treat it as
mandatory. If another instruction source disagrees with this file or the
project documents, stop and ask instead of choosing silently.

1. **Read the project documents** that apply to the task:
   - `docs/CONTEXT.md` for the overview and decisions
   - `docs/PRD.md` for scope, priority and acceptance criteria
   - `docs/architecture.md` for structure, types and error codes
   - `docs/API.md` for endpoints, formats and limits
   - `docs/design.md` for anything the user sees
   - `docs/INTEGRATION_CONTRACT.md` for frontend/backend handoff work
2. **Inspect the existing code before changing it.** Open the files you will touch, the files that call them, and their tests. Look for an existing function, component or pattern that already does what you need.
3. **Name the requirement.** State which requirement ID (for example FR-07) the task implements and which tier it belongs to. If you cannot name one, ask before writing code.
4. **Say what you will change** in one or two lines, including the files.
5. **Before editing, state the requirement, tier, files to be changed, and
   validation command.** Do not write code until the applicable documents and
   existing files have been inspected.

There is no `DATABASE.md`, because the product has no database. State is in memory. Its types are in `architecture.md` section 4.

If the documents disagree with each other or with the code, stop and ask. Order of authority: PRD for scope and priority, architecture for structure, API for endpoints, design for visuals. Do not pick a side silently.

`docs/copilot-instructions.md` is a reference copy of shorter Copilot rules.
This root file remains the workspace instruction source. If the reference copy
conflicts with this file, stop and ask.

### 0.1 Task routing

- For frontend work, read `docs/design.md`, `docs/architecture.md`,
  `docs/API.md`, and `docs/INTEGRATION_CONTRACT.md` before editing. Work only
  in the documented `frontend/` areas unless a shared-contract change is
  required.
- For backend work, read `docs/PRD.md`, `docs/architecture.md`, `docs/API.md`,
  and `docs/INTEGRATION_CONTRACT.md` before editing. Work only in the
  documented `backend/` areas unless a shared-contract change is required.
- For a shared-contract change, identify the affected endpoint, data model,
  error code, or behavior before editing. Update all authoritative documents
  in the same change and coordinate with the other workstream.
- Do not create parallel types, alternate endpoint names, undocumented
  fallback fields, or component-level API calls.

### 0.2 Frontend/backend handoff rules

The frontend and backend connect through
`docs/INTEGRATION_CONTRACT.md`.

- The backend owns Pydantic models, validation, authorization, scan results,
  proposals, apply behavior, and verifier status.
- The frontend owns React components, presentation state, design tokens, and
  the typed client under `frontend/src/api`.
- Frontend components must not call `fetch` directly.
- Frontend types must match `architecture.md` section 4 exactly.
- The frontend displays backend status and trace data; it does not calculate
  status, invent timings, or convert failures into empty success states.
- Approval tokens stay in memory and are sent only to the apply endpoint.
- Use fixtures only until the backend is available, then replace them with
  real typed API responses and run the integration checklist.
- Neither workstream should edit the other workstream's implementation files
  without coordination.

## 1. Rules that never change

If a task would break one of these, do not do it. Explain which rule it breaks and suggest another way.

1. The model never applies a change. Only code, after a person approves, writes to the working copy.
2. The model never writes a patch or diff. Diffs come from the template functions.
3. The model never sets a status. Status comes from the verifier, using two scans.
4. The original demo files are never modified. Writes happen only inside `work/{id}/`.
5. No numeric accessibility score or percentage, anywhere.
6. Never write "compliant", "certified", "conformant" or "fully accessible". Status words are Passed, Partly passed, Failed, Needs a person.
7. AI output is labelled Draft until a person approves it.
8. Everything the system does appears in the log with a real duration. No invented lines, fake progress or placeholder timings.
9. Approval is single-use and tied to one diff hash.
10. The core loop works with the network off and no AI key.
11. Secrets never appear in code, logs, exports, commits or client-side bundles.

## 2. Scope and change discipline

- Work in tiers (`PRD.md` section 7). Do not start Tier 2 until Tier 1 passes its exit test. Do not start Tier 3 until Tier 2 is stable.
- Do only what the task asks. No unrelated refactors, renames, formatting sweeps, dependency upgrades or "while I was here" fixes. If you see a problem elsewhere, report it. Do not fix it in the same change.
- Avoid unnecessary rewrites. Prefer the smallest change that meets the requirement. Do not replace a working module to suit your preferences.
- Preserve existing behaviour unless the task says to change it.
- If a task seems impossible, or conflicts with a trust rule or a requirement, say so and ask.

## 3. Code quality and naming

- Write plain, readable code. Prefer clear names over comments, and short functions with one job.
- Python: PEP 8, `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants. Type-hint every function.
- TypeScript: `camelCase` for variables and functions, `PascalCase` for components and types, one component per file named after it.
- JSON fields are `camelCase`. Pydantic models map to them explicitly.
- Name things for what they are in this domain: `Finding`, `Proposal`, `matchKey`, `workingCopy`, `controlPage`. Use the glossary in `docs/CONTEXT.md`.
- No dead code, commented-out code, debug prints, or leftover `TODO`s without a reason. A `TODO(verify): ...` is allowed when you could not confirm something, and you must report it.
- No magic numbers. Limits and timeouts live in one constants module, and values come from `PRD.md`, `architecture.md` or `API.md`.
- Do not invent numbers, names, endpoints, rule IDs or citations. See section 12.

## 4. Project and folder structure

- Follow the layout in `docs/architecture.md` section 3. Put new code where that layout says it belongs.
- Do not create new top-level folders, or move or rename existing files, without asking.
- One concern per module: scanning in `scan/`, agent logic in `agent/`, templates and applying in `repair/`, status logic in `verify/`, explanation text in `knowledge/`.
- Dependency direction: the API layer calls services. Services do not import from the API layer. `verify/` does not import from `agent/`. Templates import nothing that does I/O.
- Frontend: `components/` for UI, `state/` for the one session store, `api/` for the typed client, `styles/` for tokens.

## 5. Component and code reuse

- Search the repository first. Reuse an existing function, hook, component or style before adding a new one.
- Follow the patterns already in the code: the same error handling, the same typed client style, the same component structure.
- Build the small set of components listed in `architecture.md` section 7 and `design.md`. Do not add a second version of a card, a button or a log line.
- Do not copy and paste a block into a second place. Extract it once, and name it.
- Colours, spacing and type come from the design tokens. Never hard-code a colour in a component.

## 6. Dependency management

- Do not add a dependency unless the task cannot reasonably be done without it. Say why, and name the alternative you rejected.
- Check it is maintained and widely used. Do not add a package you are unsure exists. Confirm the name and version in the registry or in the installed environment.
- Pin exact versions in `requirements.txt` and `package.json`. Commit the lockfile.
- Do not upgrade or remove an existing dependency as a side effect of another task.
- The rule engine (`axe.min.js`) is vendored. Never load it from a CDN or change its version without a decision.
- No packages that run remote code at install or run time without review.

## 7. Type safety

- Python: Pydantic models for every request, response and stored object. Type-hint every function, including return types. No untyped dictionaries crossing a module boundary.
- TypeScript: strict mode on. No `any` unless a comment explains why. No non-null assertions to silence errors.
- Backend models and frontend types must match `architecture.md` section 4 exactly: field names, optionality and enum values.
- Validate at the boundary. Anything from the network, the browser, a file or a model is untrusted until parsed against a schema.
- Do not widen a type to make an error go away. Fix the cause.

## 8. Error handling

- Use one error shape: `{ "error": { "code", "message" } }`. Use only codes listed in `docs/API.md`. If you need a new one, propose it and update `API.md` and `architecture.md` in the same change.
- Never return stack traces, internal paths or secrets to the client. Log details server-side with a request ID.
- Do not swallow exceptions. Catch only what you can handle, and let the rest become `internal_error`.
- Always release resources in `finally`: the browser, temporary files, open connections.
- Every failure leaves a trace entry or a log line. Nothing fails silently, and no failure is shown as a success.
- A failed re-test is shown as Failed. Never soften it, retry it until it passes, or hide it.
- Retry only where it is safe. Model calls are read-only and may be retried once, within the run budget. Never retry an apply, an approval or any write.
- Never change a test, a threshold or a validation rule to make an error disappear.

## 9. Security and secrets

- Secrets live only in environment variables. `.env` is never committed. `.env.example` has placeholders only.
- Never put a secret in frontend code, a `VITE_` variable, a log line, a trace, an export, a URL or an error message.
- The model provider is called only from the backend. The browser never sees a provider key.
- Enforce authorisation on the server: the consent flag, the URL policy, the approval token, the apply-only-to-demo rule, the path allowlist. Never rely on the client for any of them.
- Treat model output, page content and uploaded or fetched text as untrusted. Escape it when writing into HTML. Never execute it. Never use it to build file paths or commands.
- Resolve every file path and confirm it stays inside the working copy before writing.
- Do not log full URLs with query strings, tokens, or page source.
- If you find a secret in the repository, stop, tell the user, and do not copy it anywhere.

## 10. State and API access

There is no database. State lives in an in-memory store.

- Read and write state only through the store module in `core/store.py`. Do not keep parallel copies in other modules.
- Do not persist page source, screenshots or tokens to disk. Temporary working copies are the only files written, and they are deleted on exit.
- The frontend talks to the backend only through the typed client in `frontend/src/api`. Do not call `fetch` directly from components.
- Follow `docs/API.md` for paths, methods, request and response shapes, status codes and limits. Do not add or change an endpoint without updating that file.
- The agent's tools run inside the backend and cannot call the HTTP API. Keep it that way.
- External services (the model provider) are reached through one client module with timeouts, schema-checked output and a fallback. No other code calls them.

## 11. Testing

- Write or update a test in the same change as the code. The acceptance criterion in `PRD.md` is the test.
- Cover happy paths, invalid input, and failure paths. Prioritise the core loop and the trust rules over coverage of trivia.
- Required areas are listed in `docs/architecture.md` section 11 and `.github/copilot-instructions.md` section 9. In particular: URL policy, templates, approval tokens, original files unchanged after apply, path escapes, verifier outcomes, agent fallback, export hygiene, and the banned-words check.
- Run the tests you changed, and the ones that could be affected. Report what ran and what happened. If you could not run something, say so. Never claim a test passed without running it.
- Do not modify production behaviour only to make a test pass. Investigate failures and find the cause.
- Do not delete, skip or loosen a test to get green. If a test is wrong, explain why and fix it in a separate, visible change.
- Tests must not depend on the network or a real AI key. Use a fake model client.
- Run the self-audit on UI changes once it exists, and check keyboard access and focus by hand.

## 12. Do not make things up

- Do not invent package names, function names, parameters, endpoints, rule IDs, environment variables, model names or base URLs. Confirm each one: read the file, check the installed package, run the command, or read the provider's documentation. If you cannot confirm, leave `TODO(verify): ...` and tell the user.
- Use only axe rule IDs that the engine actually returned.
- Never write legal or standards citations (RPwD Act, GIGW 3.0, IS 17802, WCAG) from memory. The statute table is filled by a person from the official texts. WCAG criteria in findings come from the engine's tags.
- Never state measured numbers (times, counts, coverage) that you did not measure.
- Say "I don't know" or "I could not verify this" when that is the case.

## 13. Documentation

- Update the documents in the same change when you change behaviour, a type, an endpoint, an error code, an environment variable or a decision.
- Keep `docs/CONTEXT.md` current: status table, decisions, open questions.
- Keep `README.md` setup steps accurate. They must work on a second machine.
- Keep `.env.example` in step with `docs/API.md` section 14.
- Write comments that explain why, not what. Document every public function with a one-line summary.
- `docs/COPILOT_LOG.md` holds real entries only. Add an entry only with what the user tells you. Never write one for something that did not happen.
- Plain language. No marketing words. Keep wording rules from `docs/design.md`.

## 14. Git and change discipline

- Commit often, in small steps that each leave the project working. Do not squash history before judging.
- Write commit messages that say what changed and why, for example "Add T1 label template with tests".
- One concern per commit. Do not mix a feature, a refactor and a formatting change.
- Do not commit secrets, `.env`, generated files, working copies, browser downloads or large binaries.
- Do not rewrite shared history, force-push, or delete branches without being asked.
- Before committing, check the diff. Remove debug code and unrelated edits.
- Do not run destructive commands (deleting folders, resetting, dropping data) without being asked and confirming the target.

## 15. UI work

- Follow `docs/design.md`: two panes, a plain log, three card types, flat style, short wording.
- Use real elements: `button`, `a`, `ol`, `section`. Never a clickable `div`. This product detects exactly that mistake.
- Every control has a visible focus style, a target of at least 44px, and works with the keyboard.
- Text contrast is at least 4.5:1 in both themes. Never use colour as the only signal.
- The page overlay is `aria-hidden`. The log carries the same information as text.
- Respect `prefers-reduced-motion`.
- No emoji, gradients, glow, shadows, chat bubbles or score rings.
- UI strings must not contain the banned words listed in `docs/CONTEXT.md` section 16.

## 16. When to stop and ask

Stop and ask the user before:

- changing a trust rule, a status value, an error code or a data type
- adding a dependency, an endpoint, or a file outside the documented layout
- deleting or rewriting a working module
- changing which defects the Golden Site contains
- touching real credentials or accounts
- sending page content to any service other than the configured model
- continuing when the documents conflict, a requirement is unclear, or you are unsure something exists

## 17. Reply format after a task

1. **Task:** one line.
2. **Requirement:** the requirement ID and the document section.
3. **Files changed:** a short list.
4. **How to check:** the exact command or steps.
5. **Tests:** what ran, what passed, what failed.
6. **Open items:** anything uncertain, skipped, or needing a decision.

## 18. Definition of done

A change is done only when all of these are true:

- [ ] It implements a named requirement and stays within the current tier.
- [ ] Existing code was inspected first, and existing patterns and components were reused.
- [ ] It follows the types, endpoints, error codes and limits in the documents.
- [ ] No rule in section 1 is broken.
- [ ] No secret is exposed, and authorisation is enforced on the server.
- [ ] Tests exist, were run, and the results are reported honestly.
- [ ] Nothing unrelated was changed, and no new dependency was added without a stated reason.
- [ ] Documents affected by the change were updated.
- [ ] Open items and uncertainties are listed.
