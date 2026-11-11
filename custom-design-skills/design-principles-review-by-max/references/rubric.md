# Evaluation rubric

Author of this reference: max · Part of `design-principles-review-by-max`

The four sources overlap. "Give feedback" appears in Nielsen (N1), Shneiderman (S3) and WAI (W6);
"keep it simple" in Rams (R10), Nielsen (N8) and Shneiderman (S8). Walking four lists separately
would report the same defect four times. This rubric is therefore organized **by theme**. Each
check names every framework item it tests, so a defect is reported once and counted against each
principle it breaks.

Framework IDs: `R1`–`R10` Rams (`rams.md`), `N1`–`N10` Nielsen (`nielsen.md`), `S1`–`S8`
Shneiderman (`shneiderman.md`), `W1`–`W10` W3C WAI (`wai-designing.md`).

Evidence column: **C** = source code, **S** = screenshot or design, **L** = live app. It lists the
sources that can settle the check. If none of them is available, mark the check **not assessed**;
do not guess.

## Checks

### A. Purpose and focus

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| A1 | Each screen has one evident task and one primary action that stands out from the rest. | R2, R10, N8 | S, L |
| A2 | Every element supports that task. Nothing decorative, repeated or rarely needed competes with it. | R5, R10, N8, S8 | S, L |
| A3 | Each feature and interaction answers a real user need. Novel controls are used only where they beat the standard one. | R1, R2 | S, L, C |

### B. Clarity

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| B1 | Words are the user's: labels, messages and data formats use familiar terms, with no internal names or codes. | N2, R4 | C, S, L |
| B2 | Interactive elements look interactive and are distinct from static content, with hover, focus and pressed states. | R4, W3 | L, C, S |
| B3 | Content follows the order of the task. Headings and spacing show what belongs together. | N2, W7, R4 | S, L, C |
| B4 | Icons carry a text label or are universally understood. Icon-only controls have an accessible name. | R4, N6, W9 | C, S, L |

### C. Consistency

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| C1 | The same thing looks, reads and behaves the same everywhere: terminology, component styles, placement, action sequences. | S1, N4, W3 | S, L, C |
| C2 | Navigation keeps its naming, style and position across screens, marks the current location, and offers more than one way to find content. | W4, S1, N4 | L, S |
| C3 | Platform and industry conventions are followed (see the platform reference for mobile). | N4, S1 | S, L, C |
| C4 | Visual values come from shared tokens and components, not one-off values. | R7, R8, S1 | C |

### D. Feedback and status

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| D1 | Every action gets a visible response at once, and progress is shown for anything slower than about a second. | N1, S3 | L, C |
| D2 | Each data view has designed loading, empty, error, partial and success states. | N1, S3, R8 | C, L |
| D3 | Every flow ends with clear closure: a confirmation, a reference where one exists, and a next step. | S4, N1, W6 | L, C |
| D4 | People can tell where they are: current nav item, step N of M, screen title. | N1, S3, W4 | S, L |
| D5 | Feedback is identifiable without relying on color and is exposed to assistive technology. | W6, W2 | C, L |

### E. Error prevention and recovery

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| E1 | Invalid input is prevented: constrained controls, right input types, sensible defaults, format hints, validation before submit. | N5, S5 | C, L |
| E2 | Destructive or irreversible actions are confirmed or undoable, and are visually and spatially separate from frequent actions. | N5, S5, S6 | L, S, C |
| E3 | Error messages use plain language, say what happened and how to fix it, sit beside the cause, and do not blame or alarm. | N9, S5, W6 | C, L |
| E4 | After an error the user's input is preserved. | N9, S5, S8 | L, C |
| E5 | In longer forms, errors are summarized and linked to their fields, and focus moves to the summary or first invalid field. | W6, N9 | L, C |

### F. Control and freedom

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| F1 | There is always a way out: undo, cancel, back, and a close control (and Escape on web) for every overlay. | N3, S6, S7 | L, C |
| F2 | Nothing happens that the user did not start: no surprise navigation, auto-submit, focus stealing, or auto-playing media without controls. | S7, W10, N3 | L, C |
| F3 | Long operations can be cancelled and unfinished work is kept. | N3, S6 | L, C |
| F4 | Onboarding, prompts and upsells can be skipped or dismissed. There are no forced detours. | S7, R5, R6 | L |

### G. Memory and efficiency

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| G1 | What is needed for a decision is on the screen where it is made. Nothing must be remembered between screens. | N6, S8 | S, L |
| G2 | The number of choices per view is manageable, with grouping and progressive disclosure. | S8, N8, R10 | S, L |
| G3 | Frequent users have accelerators: keyboard shortcuts, bulk actions, recents, saved filters, remembered preferences. | N7, S2 | L, C |
| G4 | Forms ask only for what is needed and help fill it: autocomplete attributes, right keyboard, defaults. | S8, N7, R2 | C, L |

### H. Honesty and restraint

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| H1 | No dark patterns: confirmshaming, pre-ticked consent, hidden costs, fake urgency or scarcity, hard-to-find cancel, disguised ads. | R6 | L, S, C |
| H2 | The interface tells the truth: labels describe what happens, progress reflects real progress, "saved" means saved. | R6, N1 | C, L |
| H3 | The product does not demand attention it has not earned: no modal on load, no permission prompt before its purpose is clear, no gratuitous motion. | R5, R10 | L, C |

### I. Visual quality and craft

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| I1 | Visual hierarchy is clear: size, weight, spacing and contrast lead the eye in order of importance. | R3, N8, W7 | S, L |
| I2 | Layout sits on a grid with a consistent spacing scale and a restrained type scale. | R3, R8 | S, C |
| I3 | Details are finished: every component state, long and short content, zero and many items, truncation with access to the full text. | R8 | L, C, S |
| I4 | The style does not trade legibility for fashion and will not date quickly. | R7, R3 | S, L |

### J. Accessibility

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| J1 | Text contrast is at least 4.5:1 (3:1 for large text). Meaningful icons, control boundaries and focus indicators reach 3:1. | W1 | L, C, S |
| J2 | Color is never the only signal for state, meaning or links. | W2 | S, L, C |
| J3 | Everything works from the keyboard (or switch / screen reader on mobile) in a logical order, with visible focus and no traps. | W3 | L, C |
| J4 | Every field has a visible label next to it that is programmatically associated. A placeholder is not a label. | W5, N6 | C, L, S |
| J5 | Images, icons and media have text alternatives. Video has captions and audio has a transcript. | W9 | C, L |
| J6 | Headings are real headings in a sensible order, and regions are marked as landmarks. | W7 | C, L |
| J7 | The layout works at different viewport sizes and text sizes: 320 CSS px wide, 200% zoom, large system font. | W8 | L, C |
| J8 | Content that starts on its own has visible stop controls, and motion honors the reduced-motion setting. | W10 | L, C |
| J9 | Pointer and touch targets are large enough and far enough apart to hit reliably (see platform sizes in `mobile.md`). | N5, R2 | L, C, S |

### K. Sustainability and help

| ID | Check | Maps to | Evidence |
| --- | --- | --- | --- |
| K1 | The product is economical with resources: right-sized images, no decorative video or heavy scripts, restrained animation. | R9 | L, C |
| K2 | Help is available where it is needed: contextual hints, useful empty states, searchable documentation. | N10 | L, S |

## Severity

One scale for every finding, from Nielsen. Rate by three factors: **frequency** (how many users
meet it), **impact** (how hard it is to get past), and **persistence** (once, or every time).

| Rating | Meaning | Typical example |
| --- | --- | --- |
| 0 | Not a problem. Recorded only to show the check was made. | A deliberate, documented deviation. |
| 1 | Cosmetic. Fix if time allows. | Uneven padding between two cards. |
| 2 | Minor. Low priority. | A vague label that people work out after a moment. |
| 3 | Major. High priority. | An error message with no way to recover; a form that loses input. |
| 4 | Catastrophe. Fix before release. | A task that cannot be completed; data loss without warning; a consent dark pattern. |

Rules that override judgment:

- A barrier that stops a group of users from finishing a task (no keyboard access, an unlabeled
  required field, unreadable contrast on essential text) is **at least 3**.
- A dark pattern around consent, payment, cancellation or data deletion is **at least 3**.
- Anything that can lose user data or money without warning is **4**.

## Recording a finding

One finding per defect, not per framework item and not per occurrence. If the same defect repeats,
record it once and list the locations.

| Field | Content |
| --- | --- |
| ID | `F-01`, `F-02`, … in order of discovery. IDs stay stable across remediation and re-evaluation. |
| Check | The rubric ID, e.g. `E3`. |
| Principles | Every framework item broken, e.g. `N9, S5, W6`. |
| Location | `file:line` for code; screen and element for screenshots and live UI. |
| Evidence | What was observed, and how (code read, screenshot, measured ratio, keyboard walk). |
| Severity | 0–4, with a one-line reason. |
| Fix | A concrete change, not "improve the error handling". |

Do not record:

- **A documented exception.** If a deviation carries a comment or decision record explaining it,
  it is a decision, not a defect. Flag it only if the reasoning is wrong, and say why.
- **What a linter, type checker or compiler already reports.**
- **Preferences.** Every finding needs an observation and its effect on the user.

## Scoring

Scores exist to show change between two runs on the same UI. They are a summary, not a
measurement; the findings are the result. Never report a score without the findings behind it.

1. For each framework item (`R1`…`W10`), take the **highest severity among open findings** that
   cite it, and convert:

   | Worst open severity | none | 1 | 2 | 3 | 4 |
   | --- | --- | --- | --- | --- | --- |
   | Item score | 100 | 85 | 60 | 30 | 0 |

2. An item whose checks were all **not assessed** is left out of the average and listed in the
   report under "Not assessed".
3. **Framework score** = mean of its assessed item scores, rounded to a whole number.
4. **Overall score** = mean of the four framework scores, rounded.
5. Verdict:

   | Overall | Verdict |
   | --- | --- |
   | 90–100 | Strong |
   | 75–89 | Sound, with issues to fix |
   | 50–74 | Needs work |
   | below 50 | Poor |

   Any open severity-4 finding caps the verdict at **Needs work**, whatever the number.

State coverage beside the score: how many of the 38 framework items were assessed. A high score on
partial evidence is not a high score.
