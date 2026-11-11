# Remediation playbook

Author of this reference: max · Part of `design-principles-review-by-max`

How to turn findings into changes. Web patterns are here; mobile patterns are in `flutter.md` and
`native-ios-android.md`.

## Rules for every fix

1. **Fix the finding, nothing else.** No redesigns, refactors or restyling beyond what the finding
   needs. Anything larger goes into the plan as a proposal for the user to decide.
2. **Stay inside the project's system.** Use its framework, component library, tokens and naming.
   Add a token or component only when none fits, and say so in the plan.
3. **Fix the cause, at the shared level.** If a button component lacks a focus style, fix the
   component, not each screen. One fix can then close several findings; list them all.
4. **Do not trade one principle for another.** Adding a confirmation dialog to every action fixes
   E2 and breaks A2 and G3. Prefer undo to confirmation for reversible actions.
5. **Keep behavior and content the user did not ask to change.** Copy changes that alter meaning
   (legal, pricing, consent) are proposed, not applied.
6. **Verify each fix against its original evidence**: the same check, with the same source.

## Order of work

Severity first (4, then 3, 2, 1). Within one severity: shared components and tokens before
individual screens, and fixes that unblock a task before fixes that polish it. Group changes so
each commit or change set closes a coherent set of findings.

## Fix patterns by rubric theme

### B, C: clarity and consistency

| Finding | Fix |
| --- | --- |
| Jargon or codes in the UI (B1) | Replace with the user's term. Map server codes to sentences in one place and keep the code only in logs or a "details" disclosure. |
| Clickable thing looks static (B2) | Use a real `<button>` or `<a>`. Give it hover, focus-visible and active styles from the design system. |
| Icon-only control (B4) | Add a visible label where space allows; otherwise `aria-label` plus a tooltip. |
| Mixed terms for one action (C1) | Pick one term, apply it in labels, messages and docs. |
| One-off colors and sizes (C4) | Replace with existing tokens. Where no token is close, propose one. |

### D: feedback and status

| Finding | Fix |
| --- | --- |
| No response to an action (D1) | Disable and mark the trigger busy (`aria-busy`, spinner inside the button), and prevent double submit. |
| Missing states (D2) | Add explicit branches for loading (skeleton or spinner with stable layout), empty (explanation and first action), error (message and retry), and partial data. |
| No closure (D3) | Add a confirmation view or message that names what was done and offers the next step. |
| Location unclear (D4) | Mark the current nav item (`aria-current="page"`), add a step indicator, set a specific page `<title>`. |
| Status not announced (D5) | Put status text in a live region (`role="status"`, or `role="alert"` for errors) and pair color with icon and text. |

### E: errors

| Finding | Fix |
| --- | --- |
| Free text for constrained data (E1) | Use the right control and input type (`type="email"`, `inputmode`, date picker, select), with a format hint. |
| Destructive action unguarded (E2) | Offer undo (toast with "Undo", soft delete) for reversible actions. Confirm only irreversible ones, naming the object and the consequence. Separate destructive buttons from primary ones and style them differently. |
| Vague error message (E3) | Rewrite as: what happened, why if known, what to do. Place it beside the field and link it with `aria-describedby`; set `aria-invalid="true"`. |
| Input lost after failure (E4) | Keep form state on error; never reset on a failed submit. |
| No error summary (E5) | Add a summary at the top of the form with links to each field, and move focus to it on submit. |

### F: control

| Finding | Fix |
| --- | --- |
| No exit from an overlay (F1) | Visible close button, Escape handler, focus returned to the trigger; use the native `<dialog>` or the library's dialog. |
| Things happen unasked (F2) | Remove auto-advance, timed redirects and focus changes on load. Autoplay only muted and with controls, or not at all. |
| Cannot cancel (F3) | Add cancel to long operations and keep a draft. |
| Forced detour (F4) | Add skip and dismiss; remember the dismissal. |

### G: memory and efficiency

| Finding | Fix |
| --- | --- |
| Must remember across screens (G1) | Carry the information forward and show it (summary panel, review step). |
| Too many choices (G2) | Group, order by frequency, and move rare options behind "More" or an advanced section. |
| No accelerators (G3) | Add keyboard shortcuts for the frequent actions and show them in tooltips or a help sheet; add bulk selection where lists are acted on. |
| Form asks too much (G4) | Remove optional fields nobody uses, add `autocomplete` tokens, set defaults. |

### H: honesty

| Finding | Fix |
| --- | --- |
| Dark pattern (H1) | Give both choices equal weight and neutral wording; untick consent by default; show the full price before commitment; make cancel as easy as sign-up. These change business behavior, so **propose them and get explicit approval**. |
| Untruthful state (H2) | Show success only after the operation succeeds; tie progress to real progress or use an indeterminate indicator. |
| Attention grabbing (H3) | Delay prompts until the user's action gives them a reason; remove modals on load. |

### I: visual craft

| Finding | Fix |
| --- | --- |
| Weak hierarchy (I1) | One primary action per view. Reduce the number of emphasized elements before adding emphasis. |
| Irregular spacing and type (I2) | Snap to the spacing and type scales already in the tokens. |
| Unfinished details (I3) | Add the missing states; handle long text with wrapping first, truncation with a title or expansion second. |

### J: accessibility

| Finding | Fix |
| --- | --- |
| Low contrast (J1) | Change the token, not the instance. Verify the new pair with `scripts/contrast.py` and check every place the token is used, in every theme. |
| Color-only meaning (J2) | Add an icon, text, underline or pattern. |
| Keyboard access (J3) | Native elements first. Otherwise `tabindex="0"`, a role, and key handlers for Enter and Space. Restore focus styles with `:focus-visible`. Fix order by fixing DOM order, never with positive `tabindex`. |
| Unlabeled field (J4) | Add a visible `<label for>`; keep placeholders for examples only. |
| Missing alternatives (J5) | Meaningful images get `alt` text that conveys their purpose; decorative ones get `alt=""`. Add captions and transcripts to media. |
| Heading structure (J6) | One `h1`, levels in order, landmarks (`header`, `nav`, `main`, `footer`). |
| Reflow (J7) | Replace fixed widths with fluid ones (`max-width`, `min()`, grid/flex wrap); allow text to wrap; test at 320px and 200% zoom. |
| Motion and autoplay (J8) | Wrap non-essential motion in `@media (prefers-reduced-motion: no-preference)`; add pause controls. |
| Small targets (J9) | Grow the hit area with padding to at least 24×24 CSS px, 44×44 for primary touch controls, with spacing between neighbors. |

### K: sustainability and help

| Finding | Fix |
| --- | --- |
| Heavy assets (K1) | Right-size and compress images, use modern formats and lazy loading, drop decorative video. |
| No help at the point of need (K2) | Add hint text under the field, an explanatory empty state, or a link to the relevant help page. |

## Framework notes

- **Angular**: prefer the component library's own states and CDK a11y utilities (`cdkTrapFocus`,
  `LiveAnnouncer`, `FocusMonitor`); bind `[attr.aria-*]`; keep error-to-sentence maps in one place
  per feature.
- **React**: use the library's accessible primitives; associate labels with `htmlFor` and `useId`;
  manage focus with refs on route change and dialog close.
- **Plain HTML/CSS**: native elements cover most of J3–J6. Reach for ARIA only when no native
  element fits.

## When not to fix

Record the finding as **open, not fixed** and explain, when the fix needs a product or legal
decision, needs content only the user can supply (real alt text for domain images, translations),
sits in third-party code, or would change an API contract. Never mark a finding closed because a
fix was attempted; mark it closed when the original check passes.
