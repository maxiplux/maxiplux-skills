import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../..');
const output = path.join(repo, '_public-site');
const original = path.join(repo, 'desing/guide-lines.html');
const sourceUrl = 'https://github.com/maxiplux/maxiplux-skills/blob/main/';
const siteUrl = 'https://maxiplux.github.io/maxiplux-skills-handbook/';
const local = href => !/^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(href);
const inside = (root, file) => file.startsWith(root + path.sep);
const slash = file => file.split(path.sep).join('/');
const assets = new Set();

// This directory contains only reproducible publishing output, never a checkout.
if (path.dirname(output) !== repo || path.basename(output) !== '_public-site' ||
    (fs.existsSync(output) && fs.lstatSync(output).isSymbolicLink()) ||
    fs.existsSync(path.join(output, '.git'))) {
  throw new Error('Refusing to replace an unexpected output directory or Git checkout');
}
fs.rmSync(output, { recursive: true, force: true });
fs.mkdirSync(output);

function pageFor(destination) {
  return fs.readFileSync(original, 'utf8')
    .replace(/\bhref="([^"]+)"/g, (match, href) => {
      if (!local(href)) return match;
      const pathname = href.split(/[?#]/)[0];
      const suffix = href.match(/[?#].*$/)?.[0] || '';
      const target = path.resolve(path.dirname(original), decodeURIComponent(pathname));
      if (!inside(repo, target) || !fs.existsSync(target)) throw new Error(`Invalid source link: ${href}`);
      const relative = slash(path.relative(repo, target));
      if (target === original ||
          (inside(path.join(repo, 'desing/assets'), target) && ['.svg', '.json'].includes(path.extname(target)))) {
        if (target !== original) assets.add(relative);
        const publicPath = slash(path.relative(path.dirname(destination), path.join(output, relative)));
        return `href="${publicPath}${suffix}"`;
      }
      return `href="${sourceUrl}${relative.split('/').map(encodeURIComponent).join('/')}${suffix}"`;
    })
    .replace(/(<h2 id="sources">[\s\S]*?<\/h2>)/,
      '$1\n<p>The handbook is public. Links to implementation sources may require access to the source repository.</p>');
}

for (const name of ['index.html', 'desing/guide-lines.html']) {
  const destination = path.join(output, name);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.writeFileSync(destination, pageFor(destination));
}
for (const relative of assets) {
  const destination = path.join(output, relative);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.copyFileSync(path.join(repo, relative), destination);
}
fs.writeFileSync(path.join(output, '.nojekyll'), '');
fs.writeFileSync(path.join(output, 'README.md'),
  `# Design without guessing\n\n[Read the illustrated handbook](${siteUrl})\n\n` +
  'A practical guide to UI/UX, AI agents, and software architecture. Includes interactive examples, illustrations, and copyable prompts.\n\n' +
  '[Download the offline HTML](./desing/guide-lines.html). Its reading content, images, styles, and interactions are embedded.\n\n' +
  'This repository hosts the generated handbook and its linked illustration assets. ' +
  '[Authoring sources](https://github.com/maxiplux/maxiplux-skills) require repository access.\n\n' +
  'GitHub Pages publishes the root of the main branch. To update, build with `npm run build:public` in the source renderer, copy the contents of `_public-site/` here, then commit and push.\n');

let checked = 0;
for (const name of ['index.html', 'desing/guide-lines.html']) {
  const file = path.join(output, name);
  const html = fs.readFileSync(file, 'utf8').replace(/<script\b[^>]*>[\s\S]*?<\/script>/g, '');
  const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]));
  for (const [, href] of html.matchAll(/\b(?:href|src)="([^"]+)"/g)) {
    if (href.startsWith('#')) {
      if (!ids.has(decodeURIComponent(href.slice(1)))) throw new Error(`Missing anchor: ${href}`);
      checked++;
    } else if (local(href)) {
      const target = path.resolve(path.dirname(file), decodeURIComponent(href.split(/[?#]/)[0]));
      if (!inside(output, target) || !fs.existsSync(target)) throw new Error(`Missing public file: ${href}`);
      checked++;
    }
  }
}
console.log(`Public bundle: two HTML editions, ${assets.size} linked illustration assets; ${checked} local links checked. No skill source code, installers, or repository history copied.`);
