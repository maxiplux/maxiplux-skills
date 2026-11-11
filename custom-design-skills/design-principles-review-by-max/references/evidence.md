# Collecting evidence

Author of this reference: max · Part of `design-principles-review-by-max`

A finding is only as good as the evidence behind it. Three sources are possible. Use every one that
is available, and state in the report which ones you had, because each source is blind to
something:

| Source | Sees well | Cannot see |
| --- | --- | --- |
| **Code** | Semantics, labels, states that exist in code, tokens, error handling, asset sizes | How it looks; whether the states are reachable; real contrast after theming |
| **Screenshots / designs** | Hierarchy, spacing, density, copy, visual consistency | Behavior, focus order, states not pictured, accessible names |
| **Live app** | Behavior, feedback timing, keyboard and focus, reflow, real colors, flows end to end | Why it happens, and where to fix it (pair it with code) |

When a check needs a source you do not have, mark it **not assessed** and name the missing source.
Do not infer rendered results from code alone ("the CSS sets `color: #999`, so contrast fails")
unless you can also establish the background it renders on.

## 1. Scope first

Before collecting anything, write down:

- **Platform**: web, Flutter, iOS, Android. For mobile, load `mobile.md` and the platform file.
- **Screens and flows in scope**. Prefer whole flows (sign up, checkout, create record) to single
  screens: closure, reversal and error recovery only show up across steps.
- **The user and their main task** for each screen. Every check is judged against it.
- **What is out of scope** (third-party widgets, legacy screens) so their absence is explicit.
- **Viewports**. For web, review at phone width (320) and desktop (1280) unless told otherwise. A
  defect that exists at only one width is still a finding: put the width in its Location, and rate
  severity for the people who use that width.

If the user gave none of this and it cannot be read from the project, ask once, briefly.

## 2. Code

Find the UI layer, then read the files for the screens in scope. Do not review the whole codebase.

| Stack | Where the UI lives |
| --- | --- |
| HTML / CSS | `*.html`, templates, stylesheets, design-token files |
| Angular | `*.html` templates, component `.ts`, `styles.*`, theme files |
| React / Vue / Svelte | components (`*.tsx`, `*.jsx`, `*.vue`, `*.svelte`), CSS modules, Tailwind config |
| Flutter | `lib/**` widgets, `ThemeData`, `*.arb` strings |
| iOS | SwiftUI views, storyboards / XIBs, asset catalogs, `Localizable.strings` |
| Android | Compose functions, `res/layout/*.xml`, `res/values/*` |

Searches that surface findings quickly (adapt the syntax to the stack):

| Looking for | Search |
| --- | --- |
| Removed focus indicators (J3, B2) | `outline:\s*(none\|0)` |
| Unlabeled inputs (J4) | inputs with `placeholder` and no `<label>`, `aria-label` or `aria-labelledby` |
| Images without alternatives (J5) | `<img` without `alt`; icon buttons with no text or accessible name |
| Clickable non-controls (J3) | `(click)=` / `onClick` on `div` or `span` without `role` and `tabindex` |
| Generic or raw errors (E3) | "Something went wrong", "Error:", `error.message` rendered directly, status codes in templates |
| Missing states (D2) | data fetches with no loading / empty / error branch in the template |
| One-off values (C4) | hex colors and pixel values outside token or theme files |
| Motion without opt-out (J8) | animations and transitions with no `prefers-reduced-motion` handling |
| Auto behavior (F2) | `autoplay`, `setInterval`, timed redirects, `focus()` on load |
| Destructive actions (E2) | delete / remove handlers with no confirm or undo |
| Fixed sizes that break reflow (J7) | fixed `width` / `height` in px on containers; `overflow: hidden` on text |

Cite `file:line` for every code finding.

## 3. Screenshots and designs

When the user supplies images, or when you capture them from the live app:

- Read each image for hierarchy, grouping, density, copy and consistency **across** images.
- Note what each image cannot tell you (focus, hover, error and empty states unless pictured).
- Estimate contrast only as a prompt to measure. Take the colors from code or the live app and
  compute the ratio. A ratio read from a compressed screenshot is not evidence.
- Identify elements by screen and a plain description ("Checkout, step 2, the secondary button
  under the card form").

## 4. Live app

Use the live app whenever it can run. This is the only source for behavior.

**Web.** If the project has a run skill or documented start command, use it. Otherwise look at
`package.json` scripts or the framework default. For a static page, open the file directly. Then
drive it with Playwright if it is available in the environment. Do not install a browser or
Playwright into the user's project just for the review; if it is missing, say so and fall back to
code and screenshots.

`scripts/capture.mjs` collects most of what the rubric needs in one pass. At each viewport width
(320 and 1280 by default) it takes a screenshot, checks for horizontal overflow, walks the keyboard
focus order, and records every text color with the background behind it. It also records the page's
headings, landmarks, unlabeled inputs and images without alternatives.

```bash
node <skill-dir>/scripts/capture.mjs <url> <output-dir>
node <skill-dir>/scripts/capture.mjs <url> <output-dir> --scope "main form" --widths 320,768,1280
python3 <skill-dir>/scripts/contrast.py --report <output-dir>/report.json
```

- Write the output to a scratch directory, not into the project.
- The script looks for Playwright in the current directory, beside itself, and in the global npm
  root. If the project depends on Playwright, run the command from the project root.
- **Scope long pages.** On a page with hundreds of controls, pass `--scope <css selector>` for each
  section under review. The focus walk, colors and headings are then limited to that element, and
  a second screenshot shows it. Without a scope the walk stops after `--max-stops` (150) stops.
- Screenshots are of the viewport, never the full page: full-page images of long pages are too
  large to read. To see another part of the page, scope to it, or scroll and capture it yourself.

Reading `report.json` (`widths.<width>` holds the per-viewport results):

- `horizontalOverflow: true` at 320 is a J7 finding. It reports the page as a whole; a table or
  code block that scrolls inside its own container is not overflow, and one that pushes content
  off-screen without a scroll container is. Check wide elements on the screenshot.
- `focusWalk.truncated: true` means the walk hit the limit before the end of the page. Say so in
  the coverage notes, or re-run with a scope.
- `focusOrder`: an empty list on a page with controls is a J3 finding. Each stop has
  `focusChange`: whether any style on the element or its three nearest ancestors differs between
  the focused and resting states. `focusChange: false` is a **candidate** J3/B2 finding, not a
  finding yet, because an indicator drawn with a pseudo-element is not detected. Focus that element
  and take a screenshot before reporting it. `focusChange: true` says something changes, not that
  the change is visible enough: `outlineColor` against `surround` should reach 3:1.
- `width` / `height` under 24px on a stop is a J9 candidate. Links inside a sentence are exempt
  from the target-size minimum; standalone links, buttons and icons are not.
- A stop with an empty `name` is a J4/J5 candidate: check its accessible name in code.
- `colors`: each entry is a text color as rendered (alpha and CSS `opacity` applied, SVG text read
  from its `fill`) and the background behind it, both resolved to opaque `rgb()`. `contrast.py --report` checks them all against the AA thresholds and lists the failures.
  Background images and gradients are not seen (the nearest solid color is reported), and text
  inside closed panels is measured in its hidden state, so check those on the screenshot.
- `contrast.py --report` also lists non-text candidates: form-field boundaries and focus outlines
  under 3:1. These need a look at the screenshot before they become findings.
- Things the script does not measure: contrast of icons and of state indicators such as a selected
  tab or current nav item (J1, J2), anything behind hover, and content that appears only after an
  interaction. Measure those by hand: read the two colors from code or the page and run
  `contrast.py`.
- Elements that exist at only one width (a phone menu, a desktop sidebar) appear only in that
  width's results. Compare the two `focusOrder` lists to find navigation that disappears at a
  width with nothing to replace it (C2).

The script loads one URL. Flows need you to drive them: fill the form wrongly and submit (E1–E5),
complete it (D3), go back mid-flow (F1), cancel (F3), throttle or block the API to see loading and
error states (D2), and emulate `prefers-reduced-motion` (J8). Capture a screenshot at each step and
record what happened.

**Web pages at phone width are still web.** Judge them with this file and the WCAG target size
(24 × 24 CSS px minimum, 44 × 44 recommended for primary controls). The mobile references are for
native and Flutter apps.

**Mobile.** Run on a simulator or emulator when the toolchain is present, and use the platform's
own inspection tools listed in `flutter.md` and `native-ios-android.md`. If the app cannot be run
in this environment, review code and any supplied screenshots, and mark behavioral checks as not
assessed.

## 5. Keep an evidence log

For each rubric check, note its result (met, finding, not assessed, or not applicable), the source
used, and the finding IDs raised. Keep the log with the evidence files. The report's "Coverage"
table summarizes it by theme, and the log is what lets a later re-evaluation repeat the same checks
the same way.
