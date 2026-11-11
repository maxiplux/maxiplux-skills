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
// Exit status: 0 done, 2 wrong usage or Playwright not found.
//
// Needs Playwright. It is looked up in the current directory, next to this script, and in the
// global npm root. Nothing is installed.

import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';

const USAGE = 'Usage: node capture.mjs <url> [out-dir] [--scope <css selector>] [--widths 320,1280] [--max-stops 150]';

// A problem with how the script was called. Reported without a stack trace, exit status 2.
class UsageError extends Error {}

function loadPlaywright() {
  const bases = [`${process.cwd()}/`, import.meta.url];
  try { bases.push(`${execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()}/`); } catch { /* no npm */ }
  for (const base of bases) {
    try { return createRequire(base)('playwright'); } catch { /* try the next location */ }
  }
  throw new UsageError('Playwright was not found. Run this from a project that depends on it, or review from code and screenshots.');
}

function parseArgs(argv) {
  const args = [...argv];
  const option = (name, fallback) => {
    const i = args.indexOf(name);
    if (i === -1) return fallback;
    const value = args[i + 1];
    if (value === undefined || value.startsWith('--')) throw new UsageError(`${name} requires a value.\n${USAGE}`);
    args.splice(i, 2);
    return value;
  };
  const scope = option('--scope', null);
  const widths = option('--widths', '320,1280').split(',').map(Number);
  const maxStops = Number(option('--max-stops', '150'));
  const unknown = args.find((a) => a.startsWith('--'));
  if (unknown) throw new UsageError(`Unknown option ${unknown}.\n${USAGE}`);
  const [url, out = 'evidence'] = args;
  if (!url) throw new UsageError(USAGE);
  if (!widths.length || widths.some((w) => !Number.isInteger(w) || w < 200)) throw new UsageError('--widths takes whole numbers of CSS px, e.g. 320,1280');
  if (!Number.isInteger(maxStops) || maxStops < 1) throw new UsageError('--max-stops takes a whole number, e.g. 150');
  return { url, out, scope, widths, maxStops };
}

// Helpers installed in the page. Colors are resolved to opaque sRGB so contrast.py can read them.
const installHelpers = () => {
  const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const cache = new Map();
  const toRgba = (css) => { // any CSS color (oklab, color-mix, named…) -> [r, g, b, a]; not a color -> transparent
    if (cache.has(css)) return cache.get(css);
    let value = [0, 0, 0, 0];
    if (CSS.supports('color', css)) {
      ctx.clearRect(0, 0, 1, 1);
      ctx.fillStyle = css;
      ctx.fillRect(0, 0, 1, 1);
      const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
      value = [r, g, b, a / 255];
    }
    cache.set(css, value);
    return value;
  };
  // Straight-alpha "over": top layer on a bottom layer, both [r, g, b, a].
  const over = (top, bottom) => {
    const a = top[3] + bottom[3] * (1 - top[3]);
    if (a === 0) return [0, 0, 0, 0];
    return [0, 1, 2].map((i) => (top[i] * top[3] + bottom[i] * bottom[3] * (1 - top[3])) / a).concat(a);
  };
  // What is painted at a point inside el: every ancestor's background from the page root up to el,
  // each group faded by its CSS opacity, then (optionally) a color drawn on top inside el.
  const paint = (el, inkCss = null) => {
    let layer = null; // the subtree painted so far, innermost first
    for (let n = el; n; n = n.parentElement) {
      const cs = getComputedStyle(n);
      let group = toRgba(cs.backgroundColor);
      if (n === el && inkCss) group = over(toRgba(inkCss), group);
      if (layer) group = over(layer, group);
      layer = [group[0], group[1], group[2], group[3] * parseFloat(cs.opacity || '1')];
    }
    return over(layer, [255, 255, 255, 1]).slice(0, 3).map(Math.round);
  };
  const backgroundOf = (el) => paint(el);
  const rgb = (c) => `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
  const textOf = (el) => (el.innerText ?? el.textContent ?? '').trim(); // SVG elements have no innerText
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
  window.__review = { toRgba, paint, backgroundOf, rgb, textOf, signature, stops: [] };
};

async function captureWidth(browser, { url, out, scope, maxStops }, width, wantSemantics) {
  const page = await browser.newPage({ viewport: { width, height: width < 600 ? 640 : 800 } });
  await page.goto(url, { waitUntil: 'load' });
  await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
  await page.screenshot({ path: `${out}/${width}-top.png` });
  if (scope) {
    const found = await page.evaluate((s) => { const el = document.querySelector(s); el?.scrollIntoView({ block: 'start' }); return !!el; }, scope);
    if (!found) throw new UsageError(`--scope ${scope} matches nothing at ${width}px`);
    await page.screenshot({ path: `${out}/${width}-scope.png` });
    await page.evaluate(() => window.scrollTo(0, 0));
  }

  const result = { viewport: page.viewportSize() };
  result.horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);

  // Focus styles are often animated. Switch transitions off so computed styles are final when read.
  await page.addStyleTag({ content: '*,*::before,*::after{transition:none!important;animation:none!important}' });
  await page.evaluate(installHelpers);

  // Text color pairs: the color as rendered (after alpha and opacity) and the background behind it.
  result.colors = await page.evaluate((s) => {
    const { toRgba, paint, rgb, textOf } = window.__review;
    const root = s ? document.querySelector(s) : document.body;
    const seen = new Map();
    for (const el of [root, ...root.querySelectorAll('*')]) {
      const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
      if (!hasText || !el.getClientRects().length) continue;
      const cs = getComputedStyle(el);
      const ink = el instanceof SVGElement ? cs.fill : cs.color; // SVG text is painted with fill
      if (toRgba(ink)[3] === 0 || cs.visibility === 'hidden') continue;
      const background = rgb(paint(el));
      const color = rgb(paint(el, ink));
      const key = `${color}|${background}|${cs.fontSize}|${cs.fontWeight}`;
      if (!seen.has(key)) seen.set(key, { color, background, fontSize: cs.fontSize, fontWeight: cs.fontWeight, sample: textOf(el).slice(0, 40), count: 0 });
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
      const { toRgba, paint, backgroundOf, rgb, textOf, signature, stops: seen } = window.__review;
      const el = document.activeElement;
      if (!el || el === document.body || seen.includes(el)) return { end: true }; // finished, or wrapped around
      seen.push(el);
      const root = s ? document.querySelector(s) : document.body;
      if (!root.contains(el)) return { skip: true };
      const cs = getComputedStyle(el);
      const box = el.getBoundingClientRect();
      const parent = el.parentElement;
      const surround = parent ? backgroundOf(parent) : [255, 255, 255];
      const hasOutline = cs.outlineStyle !== 'none' && toRgba(cs.outlineColor)[3] > 0;
      const hasBorder = parseFloat(cs.borderTopWidth) > 0 && toRgba(cs.borderTopColor)[3] > 0;
      return {
        stop: {
          index: seen.length,
          tag: el.tagName.toLowerCase(),
          role: el.getAttribute('role'),
          name: (el.getAttribute('aria-label') || textOf(el) || el.getAttribute('title') || el.getAttribute('alt') || el.getAttribute('placeholder') || '').trim().slice(0, 60),
          width: Math.round(box.width),
          height: Math.round(box.height),
          outline: `${cs.outlineStyle} ${cs.outlineWidth}`,
          outlineColor: hasOutline ? rgb(parent ? paint(parent, cs.outlineColor) : toRgba(cs.outlineColor).slice(0, 3)) : null,
          fill: rgb(backgroundOf(el)),
          border: hasBorder ? rgb(paint(el, cs.borderTopColor)) : null,
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

  let semantics = null;
  if (wantSemantics) {
    semantics = await page.evaluate((s) => {
      const { textOf } = window.__review;
      const root = s ? document.querySelector(s) : document.body;
      const within = (selector) => [...(root.matches(selector) ? [root] : []), ...root.querySelectorAll(selector)];
      const count = (list) => list.reduce((acc, k) => ({ ...acc, [k]: (acc[k] || 0) + 1 }), {});
      return {
        title: document.title,
        lang: document.documentElement.lang || null,
        headings: within('h1,h2,h3,h4,h5,h6').map((h) => `${h.tagName} ${textOf(h).slice(0, 50)}`),
        landmarks: count([...document.querySelectorAll('header,nav,main,footer,aside,[role=banner],[role=navigation],[role=main],[role=contentinfo],[role=complementary],[role=search]')].map((e) => e.getAttribute('role') || e.tagName.toLowerCase())),
        imagesWithoutAlt: within('img:not([alt])').length,
        inputsWithoutLabel: within('input:not([type=hidden]),select,textarea').filter((i) => !i.labels?.length && !i.getAttribute('aria-label') && !i.getAttribute('aria-labelledby')).length,
        autoplayMedia: within('video[autoplay],audio[autoplay]').length,
      };
    }, scope);
  }
  await page.close();
  return { result, semantics };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const { chromium } = loadPlaywright();
  mkdirSync(options.out, { recursive: true });
  const report = { url: options.url, scope: options.scope, widths: {}, semantics: {} };
  const browser = await chromium.launch();
  try { // the browser is closed however the run ends
    for (const width of options.widths) {
      const last = width === options.widths[options.widths.length - 1];
      const { result, semantics } = await captureWidth(browser, options, width, last);
      report.widths[width] = result;
      if (semantics) report.semantics = semantics;
    }
  } finally {
    await browser.close();
  }
  writeFileSync(`${options.out}/report.json`, JSON.stringify(report, null, 2));
  console.log(`Wrote ${options.out}/report.json and screenshots for widths ${options.widths.join(', ')}`);
}

try {
  await main();
} catch (error) {
  if (!(error instanceof UsageError)) throw error;
  console.error(error.message);
  process.exitCode = 2;
}
