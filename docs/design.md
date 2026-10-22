# AccessPilot design.md

Instructions for building the AccessPilot interface. Read this whole file before writing UI code. If a rule here conflicts with an older PRD or design note, this file wins.

Working name for the design: **Open Workbench**.

---

## 1. The one idea

The screen has two panes. On the left is the real page being checked. On the right is a plain log. **Nothing happens in the product that isn't written in the log first.** The person using it can always see what is being checked, what the AI did, what they decided, and what the re-test found.

Everything below serves that idea.

## 2. Principles (use these to settle any argument)

1. **Show it, don't summarise it.** If the scanner checks an element, draw a box on it. If the keyboard walk moves, show the focus ring moving. No fake progress bars.
2. **The log is the interface.** Anything the system or the AI does appears as a log line, with who did it and how long it took.
3. **The human decides.** The log stops at a "Your turn" card before any change. Nothing continues until the person picks Approve, Edit or Skip.
4. **The AI is visibly different from evidence.** AI output always has a dashed border and the word "Draft". Scanner output never does.
5. **Failure looks as honest as success.** A failed re-test is shown as clearly as a passed one.
6. **No scores, no "compliant", no "accessible".** Use counts and plain statements. See section 12 for the wording rules.
7. **Quiet by default, detail on request.** Short lines on screen. Raw detail sits behind a "Show" link.
8. **It must not look AI-made.** No gradients, glow, glass, sparkle icons, chat bubbles, emoji, or score rings.
9. **The interface must pass its own audit.** An accessibility checker with an inaccessible UI loses the demo.

## 3. Layout

One screen, two panes, one thin top bar.

```
+-------------------------------------------------------------+
| AccessPilot   [ URL or file ]  [ I'm authorised ]  [ Scan ]  |
| Scan  >  Review  >  Your decision  >  Re-test               |
+------------------------------+------------------------------+
|                              |  Log                         |
|  THE REAL PAGE               |  Scanner  Loaded page   0.4s |
|  (live iframe, with boxes    |  Scanner  Checked 212 items  |
|   drawn on what is checked)  |  Scanner  Found 5 issues     |
|                              |  Agent    Reading issue 1    |
|                              |  Agent    Drafted a fix  Show|
|                              |  +------------------------+  |
|                              |  | Your turn              |  |
|                              |  | ...                    |  |
|                              |  | [Approve] [Edit] [Skip]|  |
|                              |  +------------------------+  |
+------------------------------+------------------------------+
| Menu (top right): Coverage - Keyboard path - Export - Theme  |
+-------------------------------------------------------------+
```

- **Left pane (about 55% width):** the page under test in an `<iframe>`. Draw an overlay of boxes and numbers on top of it. The overlay is decoration for sighted users and must be hidden from assistive tech (`aria-hidden="true"`), because the log carries the same information as text.
- **Right pane (about 45% width):** the log. It scrolls. New lines append at the bottom, and the pane keeps the newest card in view.
- **Top bar:** URL field, consent checkbox, Scan button, and four small stage dots (Scan, Review, Your decision, Re-test).
- **Menu:** a single "More" menu holds Coverage, Keyboard path, Export and the theme switch. Do not put these on the main screen.
- **Narrow screens (under 900px):** stack the panes. Page on top at about 40% height, log below.
- No sidebar, no tabs, no dashboard cards, no activity bar. If you feel you need one, put it in the log instead.

## 4. The log

The log is an ordered list (`<ol>`). Each entry is one line or one card.

### 4.1 Log line anatomy

```
[Actor tag]  Short sentence (8 words or fewer)      0.4s   Show
```

| Part | Rule |
|------|------|
| Actor tag | Text label: `Scanner`, `Agent`, `You`, `Re-test`, `System` |
| Sentence | 8 words or fewer, present or past tense, no jargon |
| Duration | Real measured time, in seconds to one decimal. Omit if the step has no duration |
| Show | Link that opens the raw detail inline (see 4.3). Only present when there is detail |

Write time as it happened. Do not pre-fill future steps or show "pending" lines for steps that have not started.

### 4.2 Actors and how they look

The actor is told apart by the tag text first and the border second. Colour is never the only signal.

| Actor | Left border | Meaning |
|-------|-------------|---------|
| Scanner | Solid grey, 2px | Deterministic evidence |
| Agent | **Dashed** amber, 2px, plus the word "Draft" on proposals | AI output, not trusted yet |
| You | Solid blue, 2px | A human decision |
| Re-test | Solid green or red, 2px, plus the word "Passed" or "Failed" | Deterministic result |
| System | No border, muted text | Housekeeping, errors, limits |

### 4.3 The "Show" link

"Show" expands a panel under the line (a disclosure button with `aria-expanded`). Contents depend on the actor:

- **Scanner:** rule ID, impact, CSS selector, code snippet (monospace), link to the rule's guidance.
- **Agent:** exactly what it was given (the evidence) and exactly what it returned (the draft). Include the tool name and its input and output.
- **You:** what was approved or edited, and the time.
- **Re-test:** the before and after finding lists, resolved, remaining and new.

Detail is collapsed by default. It must always be reachable.

### 4.4 Required log lines

The log must include a line for each of these when it really happens:

1. Page loaded (with time)
2. Checks run (number of elements checked)
3. Each finding group found (count by impact)
4. Keyboard walk started, each stop (optional, collapsed under one line), loop or trap found
5. Agent started, each tool call it makes, each draft it produces, each time it cannot do something
6. Anything blocked (for example a file outside the allowed list): shown as a `System` line saying what was blocked and why
7. Limits: one line such as "Not checked: captions, reading order, content meaning" (see section 9)
8. Your decision on each card
9. Apply (what changed in the working copy, never the original)
10. Re-test start and result

If the AI is not available (no key, outage), log it: `System  No AI model. Using built-in guidance.` The layout does not change.

## 5. Cards

Cards are the only boxed elements in the log. There are three kinds. A card is a `<section>` with a heading and is reachable by keyboard.

### 5.1 "Your turn" card (needs a decision)

Appears when a fix is proposed. The log pauses here.

```
Your turn
One sentence: what is wrong and who it blocks.
  A blind user hears "edit text" with no name.

Proposed change                         Draft
  - <input id="email">
  + <label for="email">Email</label>
  + <input id="email">

Risk: low        Template: label

[ Approve ]   [ Edit wording ]   [ Skip ]
```

Rules:

- Show the **exact diff** that will be applied. Use `+` and `-` characters at line start, plus colour. Never colour alone.
- Show the one-sentence impact line ("who is blocked and from doing what"). Keep it under 15 words.
- Approve, Edit and Skip are real `<button>` elements, at least 44px tall.
- **Edit wording** opens a single text field for the wording the human controls (alt text, label text). Changing it regenerates the diff before approval. Only these values are editable. The person does not hand-edit code.
- The card shows "Draft" in the dashed amber style until the person approves. After approval the border becomes solid blue and the line reads `You  Approved fix 1`.
- Approval is single-use and tied to this exact diff. If the diff changes, the old approval is void.

### 5.2 "Needs a person" card (no fix offered)

For anything the system will not fix: clickable `div` without keyboard support, focus loops, missing landmarks, heading order, meaningless alt text, content judgement.

```
Needs a person
Why: no safe automatic fix for this.
What was found: Clickable div is not reachable by Tab.
Where: #submit-btn
```

There is **no Approve button** on this card. It has a "Mark as noted" button only. Never hide these cards.

### 5.3 "Result" card (after the re-test)

```
Re-test: Passed        (or: Failed / Partly passed / Needs a person)
Resolved 1    Remaining 4    New 0
Control page: no new issues

Before:  <input id="email">   announced as "edit text"
After:   <input id="email">   announced as "Email, edit text"
```

Rules:

- The status word comes only from the deterministic re-scan. The AI never sets it.
- Four possible words: `Passed`, `Partly passed`, `Failed`, `Needs a person`. Always shown with an icon and the word.
- Counts are plain numbers. No percentages, rings or gauges.
- The "After" announcement line is an approximation of a screen reader, built from the accessibility tree. Label it "Approximate". Optional play button uses the browser's speech synthesis, with the text visible.
- A failed result stops the stage dots at the failed stage and shows the reason. It is as prominent as a pass.

## 6. The page pane

- Load the page under test in a sandboxed `<iframe>`. For the demo, this is the bundled Golden Site and its patched working copy.
- During the scan, draw a thin box on each element as it is checked. Boxes are 2px outlines with a small number tag. They stay only for findings after the scan ends.
- Clicking a box scrolls the log to that finding's card and moves focus to its heading. Clicking a finding in the log highlights its box. Keep them in sync.
- **Keyboard walk view:** draw a line through the tab stops in order, with a number on each stop. Show the focus ring moving during the walk. Mark repeated stops (loops) with a different outline style, and say so in the log.
- **Before and after:** after a re-test, the iframe reloads the patched copy. A small toggle ("Original / Patched") switches between them.
- Provide a text alternative for everything the overlay shows (the log lines).

## 7. Stage dots (top bar)

Four dots: **Scan, Review, Your decision, Re-test.**

- A dot fills only when that stage has really completed.
- The active stage has a visible outline.
- If a stage fails, the dot shows the failure icon and the word, and later dots stay empty.
- Each dot has a text label. The dots are decoration over a text list, so expose them as an ordered list with `aria-current="step"` on the active one.
- No animation beyond a simple fill. No percentage.

## 8. Visual style

Flat, quiet, plain. Closer to a ship's log or a terminal history than to a dashboard.

| Property | Value |
|----------|-------|
| Corners | 4px (6px maximum) |
| Borders | 1px, thin, neutral |
| Shadows | None |
| Gradients, blur, glow | None |
| Icons | A few line icons for status only (check, cross, warning, pause). Always next to a word |
| Emoji | None |
| Spacing | 8px base unit. 16px between log lines, 24px around cards |
| Page background | Off-white (light theme), near-black (dark theme) |

### 8.1 Colour tokens

Define these as CSS custom properties on `:root`. Dark values go under `@media (prefers-color-scheme: dark)` and a `[data-theme="dark"]` override. Default theme is **light** (it survives venue projectors better). Provide a visible theme switch in the More menu.

| Token | Light | Dark | Used for |
|-------|-------|------|----------|
| `--bg` | `#FAFAF8` | `#12161C` | App background |
| `--surface` | `#FFFFFF` | `#1A2029` | Cards, log panel |
| `--text` | `#1B1F24` | `#E6EAF0` | Body text |
| `--muted` | `#5A6270` | `#A3ADBB` | Secondary text, System lines |
| `--border` | `#D6D9DE` | `#2F3744` | Hairlines |
| `--accent` | `#1F5FBF` | `#6EA8FF` | You, buttons, links, focus ring base |
| `--evidence` | `#4B5563` | `#B4BDCA` | Scanner border and tag |
| `--draft` | `#8A5A00` | `#F2C14E` | Agent border and "Draft" tag |
| `--draft-bg` | `#FFF6E0` | `#2A2412` | Background tint of draft cards |
| `--pass` | `#1E7B3A` | `#5FD08A` | Passed |
| `--fail` | `#B3261E` | `#FF8A80` | Failed |

Contrast rules:

- Body text and any text-on-background pair must reach **4.5:1** or better. Large text and UI borders need 3:1.
- Check every pair above and every pair you add with a contrast tool before the demo. The values in the table are starting points, not proof.
- Never use colour as the only signal. Every colour has an accompanying word or icon.

### 8.2 Type

- **UI text:** system font stack, Segoe UI first (`"Segoe UI", system-ui, -apple-system, Roboto, sans-serif`). Body 16px minimum, line height 1.5.
- **Code, selectors, diffs, snippets:** monospace (`"JetBrains Mono", Consolas, "Courier New", monospace`), 14px minimum.
- Headings are small and plain: card title 18px semibold, nothing larger than 24px anywhere. No marketing headlines.
- Sentence case everywhere. No all-caps labels.

### 8.3 Focus

- Every interactive element has a visible focus style: 3px outline using `--accent`, 2px offset. Never remove it.
- Focus is visible against both themes and against the iframe overlay.

### 8.4 Motion

- Allowed: log lines appear without animation, stage dots fill, the keyboard path line draws in tab order.
- All motion is off when `prefers-reduced-motion: reduce` is set. The information must still appear.
- No spinners that imply progress. While waiting for a real step, show a text line such as `Scanner  Checking elements...` that gets its time added when it finishes.

## 9. Coverage and limits

Coverage is honest and small. It lives in the More menu, and one summary line appears in the log after every scan.

The coverage view lists three groups:

1. **Ran:** the checks that ran (rule engine and version, number of rules, keyboard walk).
2. **Did not run:** things this tool does not test (captions, reading order, content meaning, real screen readers, assistive technology other than the keyboard).
3. **Needs a person:** items the engine flagged as uncertain, plus anything in a "Needs a person" card.

No score. No percentage. No "X% accessible".

## 10. States

| State | What the person sees |
|-------|----------------------|
| Nothing scanned yet | Page pane shows a short prompt. Log shows `System  Enter a URL and confirm you are authorised.` |
| Scanning | Button reads "Scanning..." and is disabled. Log lines appear as steps finish |
| AI unavailable | `System` line explaining why. Built-in guidance cards appear in the same layout |
| Fix proposed | "Your turn" card. Log is paused |
| Needs a person | "Needs a person" card with no Approve button |
| Applying | `System  Applying to working copy...` then a time |
| Re-test passed | Result card, green, with the word "Passed" |
| Re-test failed | Result card, red, with the word "Failed", the reason, and counts |
| API unreachable | `System` line: "Cannot reach the AccessPilot API. Is the backend running on port 8000?" |
| Consent missing | `System` line with the error code `consent_required`. Scan does not start |
| Budget reached | `System` line: the agent hit its turn, tool or time limit. Built-in guidance fills the rest |

## 11. Accessibility requirements for AccessPilot's own UI

These are not optional. Build them in from the first commit.

- One `<h1>` (the app name). Log cards use `<h2>` or `<h3>`.
- Landmarks: `<header>`, `<main>` (holds both panes), and a labelled region for the log and one for the page pane.
- A skip link as the first focusable element ("Skip to log").
- The log is a live region (`role="log"` with `aria-live="polite"`). New lines are announced. Do not announce every keyboard-walk stop. Announce the summary line.
- When the log pauses on a card, move focus to the card heading. After a decision, return focus to the next log line.
- All controls work with the keyboard. Disclosures use real buttons with `aria-expanded`.
- Target size 44px minimum for buttons.
- The diff is real text with `+` and `-` markers, not an image.
- The iframe has a `title`. The overlay is `aria-hidden` and duplicates nothing that the log doesn't already say.
- Text can scale to 200% without breaking the layout.
- Run axe and a manual keyboard pass on the UI before every demo rehearsal. Target: zero serious or critical findings.

## 12. Wording rules

Short, plain, human. The UI is not a pitch deck.

- Log sentences: 8 words or fewer.
- Impact lines: one sentence, under 15 words, naming the person and the blocked action. Example: "A keyboard user can't reach Submit."
- Hide rule IDs, selectors and citations behind "Show".
- Say "Passed", "Partly passed", "Failed", "Needs a person". Never say "Fixed everywhere", "Accessible", "Compliant", "Certified" or "WCAG conformant".
- Statute references (RPwD Act, GIGW 3.0, IS 17802) appear only inside "Show", as citations, with the line "Reference only. Not a compliance claim."
- AI text always carries "Draft" until a human approves it.
- No exclamation marks. No "Awesome!", "Great job!" or similar.
- No jargon in the main line. "Label" not "accessible name". "Keyboard user" not "non-pointer user".

## 13. Data to UI mapping

| Backend object | Shown as |
|----------------|----------|
| Trace entry (step, actor, duration, ok) | One log line |
| Finding | A box on the page, a `Scanner` log line, and (if repairable) a "Your turn" card |
| Finding with no template | "Needs a person" card |
| Agent tool call | `Agent` log line with Show detail (input, output) |
| Proposal | "Your turn" card with diff |
| Approval | `You` log line |
| Apply result | `System` line, then "Result" card |
| Comparison (resolved, remaining, introduced) | Counts in the Result card |
| Keyboard walk stops | Numbered path on the page pane and one summary log line |
| Coverage object | More menu, plus one summary log line |

Every item above must come from real data. Do not invent log lines.

## 14. Components to build

Build in this order. Each is small.

1. `AppShell` (top bar, two panes, More menu)
2. `PagePane` (iframe, overlay layer, Original/Patched toggle)
3. `Log` and `LogLine` (live region, actor tag, duration, Show disclosure)
4. `YourTurnCard` (diff, Approve, Edit wording, Skip)
5. `NeedsPersonCard`
6. `ResultCard`
7. `StageDots`
8. `CoverageView` and `ThemeSwitch` (inside More menu)

Keep state in one place: the current scan, run trace, proposals and results. Components read from it. API calls update it. Use TypeScript types that match the API response.

## 15. Build order for the UI

1. Static layout with sample data. Check the layout and the log lines look right.
2. Wire the Scan button and show real log lines.
3. Draw the finding boxes on the iframe overlay.
4. Add "Your turn" cards with the diff and Approve.
5. Wire Approve, apply and the Result card.
6. Add "Needs a person" cards and the coverage summary line.
7. Add the keyboard path view.
8. Add the theme switch.
9. Run the axe check and a keyboard-only pass. Fix everything serious.

If time runs out, drop from the bottom of this list, never from the top.

## 16. Do and don't

| Do | Don't |
|----|-------|
| One log, everything in order | Separate dashboards for each feature |
| Dashed amber border for AI | Sparkle icons, "AI-powered" badges |
| Plain buttons: Approve, Edit, Skip | Fancy toggle switches for approval |
| Numbers (Resolved 1, Remaining 4) | Scores, rings, percentages |
| Show failures clearly | Hide or soften a failed re-test |
| Detail behind "Show" | Long paragraphs in the log |
| Real durations from the trace | Fake loading steps |
| Text label with every colour | Colour-only status |

## 17. Acceptance checklist

The design is done when all of these are true.

- [ ] Every action in a scan appears as a log line with the actor and a real time.
- [ ] The log pauses at "Your turn" and nothing changes until the person decides.
- [ ] The exact diff is shown before approval, and the approved diff is the one applied.
- [ ] The original demo files are never changed. Only the working copy is patched.
- [ ] Re-test status comes from the re-scan. The AI never sets it.
- [ ] A failed re-test is shown as clearly as a passed one.
- [ ] Items with no safe fix show "Needs a person" and no Approve button.
- [ ] AI output is visibly different (dashed border, "Draft") from scanner output.
- [ ] No score, percentage or "compliant" wording anywhere.
- [ ] Works with the AI off and the network off (built-in guidance, logged).
- [ ] Both themes pass 4.5:1 contrast for text.
- [ ] Whole flow works with the keyboard only, with visible focus.
- [ ] Reduced-motion setting removes all animation.
- [ ] axe reports zero serious or critical findings on the AccessPilot UI.
- [ ] A person seeing the screen for the first time can say what the AI did, what they approved, and what the re-test found.

## 18. Demo path (about three minutes)

1. Open the Golden Site. Press Scan. Boxes appear on the page as log lines arrive.
2. The log shows five findings and the limits line.
3. Run the agent. Tool calls stream into the log. A "Your turn" card appears for the email label.
4. Press Approve. The log shows Apply, then Re-test.
5. The Result card shows Passed, Resolved 1, New 0, and the before and after announcement lines.
6. Show a "Needs a person" card for the clickable `div`. Say plainly that the tool will not guess.
7. Open More, then Coverage, and read the "Did not run" list aloud.

## 19. Sources behind these rules

- Pause before the side effect and show the exact payload, to avoid approval after the fact (human-in-the-loop UX patterns).
- Keep and Undo per change, checkpoints, and tool confirmation (GitHub Copilot agent mode in VS Code).
- Visible state, reversible actions and understandable explanations (Microsoft HAX Toolkit, 18 guidelines for human-AI interaction).
- Highlight failures on the page and combine automated checks with a guided keyboard check (Accessibility Insights for Web).
- A perfect automated score doesn't mean accessible, so no score (Lighthouse documentation and accessibility practitioners).
- Template-based fixes with deterministic verification, because LLM patches can hallucinate edits or miss instances (A11y-Bench, AccessGuru).
- Screen reader simulation augments real testing and doesn't replace it (Guidepup virtual screen reader).
