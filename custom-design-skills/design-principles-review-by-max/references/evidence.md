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

The script below collects most of what the rubric needs in one pass: screenshots at three widths, a
horizontal-overflow check at 320px, the keyboard focus order with whether each stop has a visible
indicator, text colors for contrast measurement, and basic semantics. Save it outside the project
(a scratch directory) and run it **from the project directory**, so it finds the project's own
Playwright: `node /path/to/capture.mjs <url> <output-dir>`.

```js
// capture.mjs: evidence capture for design-principles-review-by-max
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';

// Resolve Playwright from the directory the script is run in, then from a global install.
const { chromium } = createRequire(`${process.cwd()}/`)('playwright');

const [url, out = 'evidence'] = process.argv.slice(2);
mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const report = { url, viewports: {}, focusOrder: [], colors: [], semantics: {} };

for (const [name, width, height] of [['mobile', 320, 640], ['tablet', 768, 1024], ['desktop', 1280, 800]]) {
  const page = await browser.newPage({ viewport: { width, height } });
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: true });
  report.viewports[name] = await page.evaluate(() => ({
    horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  await page.close();
}

const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto(url, { waitUntil: 'networkidle' });

// Keyboard walk: Tab through the page and record each stop.
for (let i = 0; i < 200; i++) {
  await page.keyboard.press('Tab');
  const stop = await page.evaluate(() => {
    const el = document.activeElement;
    if (!el || el === document.body || el.dataset.reviewSeen) return null; // done, or wrapped around
    el.dataset.reviewSeen = '1';
    const cs = getComputedStyle(el);
    const name = (el.getAttribute('aria-label') || el.innerText || el.getAttribute('title') || el.getAttribute('alt') || '').trim().slice(0, 60);
    return {
      tag: el.tagName.toLowerCase(), role: el.getAttribute('role'), name,
      outline: `${cs.outlineStyle} ${cs.outlineWidth} ${cs.outlineColor}`,
      boxShadow: cs.boxShadow,
      // Some designs draw the indicator on a wrapper (:focus-within), so look a few levels up.
      indicatorOnAncestor: (() => {
        for (let n = el.parentElement, i = 0; n && i < 3; n = n.parentElement, i++) {
          const p = getComputedStyle(n);
          if (p.outlineStyle !== 'none' || p.boxShadow !== 'none') return true;
        }
        return false;
      })(),
      width: Math.round(el.getBoundingClientRect().width),
      height: Math.round(el.getBoundingClientRect().height),
    };
  });
  if (!stop) break;
  report.focusOrder.push(stop);
}

// Text colors, resolved to opaque sRGB so they can be passed straight to contrast.py.
report.colors = await page.evaluate(() => {
  const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const toRgba = (css) => { // any CSS color (oklab, color-mix, named…) -> [r, g, b, a]
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = css;
    ctx.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
    return [r, g, b, a / 255];
  };
  const over = (top, under) => top.slice(0, 3).map((c, i) => Math.round(top[3] * c + (1 - top[3]) * under[i]));
  const backgroundOf = (el) => { // composite every background layer from the page up to the element
    const layers = [];
    for (let n = el; n; n = n.parentElement) layers.unshift(toRgba(getComputedStyle(n).backgroundColor));
    return layers.reduce((under, layer) => over(layer, under), [255, 255, 255]);
  };
  const rgb = (c) => `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
  const seen = new Map();
  for (const el of document.querySelectorAll('body *')) {
    const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (!hasText || !el.getClientRects().length) continue;
    const cs = getComputedStyle(el);
    const text = toRgba(cs.color);
    if (text[3] === 0 || cs.visibility === 'hidden') continue;
    const bg = backgroundOf(el);
    const key = `${rgb(over(text, bg))}|${rgb(bg)}|${cs.fontSize}|${cs.fontWeight}`;
    if (!seen.has(key)) seen.set(key, { color: rgb(over(text, bg)), background: rgb(bg), fontSize: cs.fontSize, fontWeight: cs.fontWeight, sample: el.innerText.trim().slice(0, 40), count: 0 });
    seen.get(key).count++;
  }
  return [...seen.values()];
});

report.semantics = await page.evaluate(() => ({
  title: document.title,
  lang: document.documentElement.lang || null,
  headings: [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map((h) => `${h.tagName} ${h.innerText.trim().slice(0, 50)}`),
  landmarks: [...document.querySelectorAll('header,nav,main,footer,aside,[role]')].map((e) => e.getAttribute('role') || e.tagName.toLowerCase()),
  imagesWithoutAlt: [...document.querySelectorAll('img:not([alt])')].length,
  inputsWithoutLabel: [...document.querySelectorAll('input:not([type=hidden]),select,textarea')].filter((i) => !i.labels?.length && !i.getAttribute('aria-label') && !i.getAttribute('aria-labelledby')).length,
  autoplayMedia: [...document.querySelectorAll('video[autoplay],audio[autoplay]')].length,
}));

writeFileSync(`${out}/report.json`, JSON.stringify(report, null, 2));
await browser.close();
console.log(`Wrote ${out}/report.json and screenshots`);
```

Reading the output:

- `focusOrder`: an empty list on a page with controls is a J3 finding. A stop with
  `outline: none …`, `boxShadow: none` and `indicatorOnAncestor: false` is a **candidate** J3/B2
  finding, not a finding yet: some designs show focus with a border or background change the script
  does not capture. Focus that element and take a screenshot before reporting it.
- `colors`: each entry is a text color and the background behind it, already resolved to opaque
  `rgb()`. Feed each pair to `scripts/contrast.py`. Background images and gradients are not seen
  (the nearest solid color is reported), and text inside closed panels is measured in its hidden
  state, so check those on the screenshot.
- `viewports.mobile.horizontalOverflow: true` is a J7 finding.
- `width` / `height` under 24px on a focus stop is a J9 candidate. Links inside a sentence are
  exempt from the target-size minimum; standalone links, buttons and icons are not.
- A focus stop with an empty `name` is a J4/J5 candidate: check its accessible name in code.

The script loads one URL. Flows need you to drive them: fill the form wrongly and submit (E1–E5),
complete it (D3), go back mid-flow (F1), cancel (F3), throttle or block the API to see loading and
error states (D2), and emulate `prefers-reduced-motion` (J8). Capture a screenshot at each step and
record what happened.

**Mobile.** Run on a simulator or emulator when the toolchain is present, and use the platform's
own inspection tools listed in `flutter.md` and `native-ios-android.md`. If the app cannot be run
in this environment, review code and any supplied screenshots, and mark behavioral checks as not
assessed.

## 5. Keep an evidence log

For each rubric check, note: assessed or not, the source used, and the finding IDs raised. The log
becomes the "Coverage" section of the report, and it is what lets a later re-evaluation repeat the
same checks the same way.
