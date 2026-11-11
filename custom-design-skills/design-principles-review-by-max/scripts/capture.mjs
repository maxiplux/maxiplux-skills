#!/usr/bin/env node
// Evidence capture for the design-principles-review-by-max skill. Author: max.
//
// Loads a page at each requested width and writes, into the output directory:
//   <width>-top.png      viewport screenshot of the top of the page
//   <width>-scope.png    viewport screenshot with the scoped element scrolled into view (with --scope)
//   report.json          per width: horizontal overflow, keyboard focus order, text color pairs;
//                        once: title, language, headings, landmarks, unlabeled inputs, images without alt
//
// Usage:
//   node capture.mjs <url> [out-dir] [--scope <css selector>] [--widths 320,1280] [--max-stops 150]
//
//   --scope      limit the focus walk, colors and headings to one element (a section, a form, a dialog)
//   --widths     viewport widths in CSS px; default 320,1280 (phone and desktop)
//   --max-stops  stop the keyboard walk after this many recorded stops; default 150
//
// Needs Playwright. It is looked up in the current directory, next to this script, and in the
// global npm root. Nothing is installed.

import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';

function loadPlaywright() {
  const bases = [`${process.cwd()}/`, import.meta.url];
  try { bases.push(`${execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()}/`); } catch { /* no npm */ }
  for (const base of bases) {
    try { return createRequire(base)('playwright'); } catch { /* try the next location */ }
  }
  console.error('Playwright was not found. Run this from a project that depends on it, or review from code and screenshots.');
  process.exit(2);
}

const args = process.argv.slice(2);
const option = (name, fallback) => {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args.splice(i, 2)[1];
};
const scope = option('--scope', null);
const widths = option('--widths', '320,1280').split(',').map(Number);
const maxStops = Number(option('--max-stops', '150'));
const [url, out = 'evidence'] = args;
if (!url) {
  console.error('Usage: node capture.mjs <url> [out-dir] [--scope <css selector>] [--widths 320,1280] [--max-stops 150]');
  process.exit(2);
}

const { chromium } = loadPlaywright();
mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const report = { url, scope, widths: {}, semantics: {} };

// Helpers installed in the page. Colors are resolved to opaque sRGB so contrast.py can read them.
const installHelpers = () => {
  const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const toRgba = (css) => { // any CSS color (oklab, color-mix, named…) -> [r, g, b, a]
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = css;
    ctx.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
    return [r, g, b, a / 255];
  };
  const over = (top, under) => top.slice(0, 3).map((c, i) => Math.round(top[3] * c + (1 - top[3]) * under[i]));
  const backgroundOf = (el) => { // composite every background layer from the page root up to el
    const layers = [];
    for (let n = el; n; n = n.parentElement) layers.unshift(toRgba(getComputedStyle(n).backgroundColor));
    return layers.reduce((under, layer) => over(layer, under), [255, 255, 255]);
  };
  const rgb = (c) => `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
  // Everything that commonly changes to show focus, on the element and three ancestors.
  const signature = (el) => {
    const parts = [];
    for (let n = el, i = 0; n && i < 4; n = n.parentElement, i++) {
      const cs = getComputedStyle(n);
      parts.push([cs.outlineStyle, cs.outlineWidth, cs.outlineColor, cs.boxShadow, cs.borderTopColor,
        cs.borderBottomColor, cs.borderBottomWidth, cs.backgroundColor, cs.color, cs.textDecorationLine].join('|'));
    }
    return parts.join(' / ');
  };
  window.__review = { toRgba, over, backgroundOf, rgb, signature, stops: [] };
};

for (const width of widths) {
  const page = await browser.newPage({ viewport: { width, height: width < 600 ? 640 : 800 } });
  await page.goto(url, { waitUntil: 'load' });
  await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
  await page.screenshot({ path: `${out}/${width}-top.png` });
  if (scope) {
    const found = await page.evaluate((s) => { const el = document.querySelector(s); el?.scrollIntoView({ block: 'start' }); return !!el; }, scope);
    if (!found) { console.error(`--scope ${scope} matches nothing at ${width}px`); process.exit(2); }
    await page.screenshot({ path: `${out}/${width}-scope.png` });
    await page.evaluate(() => window.scrollTo(0, 0));
  }

  const result = { viewport: page.viewportSize() };
  result.horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);

  // Focus styles are often animated. Switch transitions off so computed styles are final when read.
  await page.addStyleTag({ content: '*,*::before,*::after{transition:none!important;animation:none!important}' });
  await page.evaluate(installHelpers);

  // Text color pairs.
  result.colors = await page.evaluate((s) => {
    const { toRgba, over, backgroundOf, rgb } = window.__review;
    const root = s ? document.querySelector(s) : document.body;
    const seen = new Map();
    for (const el of root.querySelectorAll('*')) {
      const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
      if (!hasText || !el.getClientRects().length) continue;
      const cs = getComputedStyle(el);
      const text = toRgba(cs.color);
      if (text[3] === 0 || cs.visibility === 'hidden') continue;
      const bg = backgroundOf(el);
      const color = rgb(over(text, bg));
      const key = `${color}|${rgb(bg)}|${cs.fontSize}|${cs.fontWeight}`;
      if (!seen.has(key)) seen.set(key, { color, background: rgb(bg), fontSize: cs.fontSize, fontWeight: cs.fontWeight, sample: el.innerText.trim().slice(0, 40), count: 0 });
      seen.get(key).count++;
    }
    return [...seen.values()];
  }, scope);

  // Keyboard walk: press Tab, record each stop while it has focus.
  let tabs = 0;
  let ended = false;
  const stops = [];
  while (stops.length < maxStops && tabs < maxStops * 4) {
    await page.keyboard.press('Tab');
    tabs++;
    const step = await page.evaluate((s) => {
      const { toRgba, over, backgroundOf, rgb, signature, stops: seen } = window.__review;
      const el = document.activeElement;
      if (!el || el === document.body || seen.includes(el)) return { end: true }; // finished, or wrapped around
      seen.push(el);
      const root = s ? document.querySelector(s) : document.body;
      if (!root.contains(el)) return { skip: true };
      const cs = getComputedStyle(el);
      const box = el.getBoundingClientRect();
      const surround = el.parentElement ? backgroundOf(el.parentElement) : [255, 255, 255];
      const fill = backgroundOf(el);
      const outline = toRgba(cs.outlineColor);
      const border = toRgba(cs.borderTopColor);
      return {
        stop: {
          index: seen.length,
          tag: el.tagName.toLowerCase(),
          role: el.getAttribute('role'),
          name: (el.getAttribute('aria-label') || el.innerText || el.getAttribute('title') || el.getAttribute('alt') || el.getAttribute('placeholder') || '').trim().slice(0, 60),
          width: Math.round(box.width),
          height: Math.round(box.height),
          outline: `${cs.outlineStyle} ${cs.outlineWidth}`,
          outlineColor: cs.outlineStyle === 'none' || outline[3] === 0 ? null : rgb(over(outline, surround)),
          fill: rgb(fill),
          border: parseFloat(cs.borderTopWidth) > 0 && border[3] > 0 ? rgb(over(border, fill)) : null,
          surround: rgb(surround),
          focused: signature(el),
        },
      };
    }, scope);
    if (step.end) { ended = true; break; }
    if (step.stop) stops.push(step.stop);
  }

  // Compare each stop with its resting state: does anything visibly change when it takes focus?
  const resting = await page.evaluate(() => {
    document.activeElement?.blur();
    return window.__review.stops.map((el) => window.__review.signature(el));
  });
  for (const stop of stops) {
    stop.focusChange = stop.focused !== resting[stop.index - 1];
    delete stop.focused;
  }
  result.focusOrder = stops;
  result.focusWalk = { tabsPressed: tabs, stopsRecorded: stops.length, truncated: !ended };

  if (width === widths[widths.length - 1]) {
    report.semantics = await page.evaluate((s) => {
      const root = s ? document.querySelector(s) : document.body;
      const count = (list) => list.reduce((acc, k) => ({ ...acc, [k]: (acc[k] || 0) + 1 }), {});
      return {
        title: document.title,
        lang: document.documentElement.lang || null,
        headings: [...root.querySelectorAll('h1,h2,h3,h4,h5,h6')].map((h) => `${h.tagName} ${h.innerText.trim().slice(0, 50)}`),
        landmarks: count([...document.querySelectorAll('header,nav,main,footer,aside,[role=banner],[role=navigation],[role=main],[role=contentinfo],[role=complementary],[role=search]')].map((e) => e.getAttribute('role') || e.tagName.toLowerCase())),
        imagesWithoutAlt: root.querySelectorAll('img:not([alt])').length,
        inputsWithoutLabel: [...root.querySelectorAll('input:not([type=hidden]),select,textarea')].filter((i) => !i.labels?.length && !i.getAttribute('aria-label') && !i.getAttribute('aria-labelledby')).length,
        autoplayMedia: root.querySelectorAll('video[autoplay],audio[autoplay]').length,
      };
    }, scope);
  }
  report.widths[width] = result;
  await page.close();
}

writeFileSync(`${out}/report.json`, JSON.stringify(report, null, 2));
await browser.close();
console.log(`Wrote ${out}/report.json and screenshots for widths ${widths.join(', ')}`);
