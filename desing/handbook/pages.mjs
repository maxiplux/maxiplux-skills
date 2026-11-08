import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Marked } from 'marked';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../..');
const site = path.join(repo, '_site');
const markdown = new Marked({ gfm: true });
const sourceDocuments = [
  'README.md', 'desing/guide-lines', 'desing/ui-ux-design.md',
  'desing/ai-agents.md', 'desing/software-architecture.md', 'desing/handbook/README.md'
];
const local = href => href && !/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(href);
const inside = (root, file) => file === root || file.startsWith(root + path.sep);
const read = file => fs.readFileSync(file, 'utf8');
const errors = [];
let checked = 0;

function resolveLink(root, from, href) {
  const [pathname, fragment] = href.split('#', 2);
  const filePart = decodeURIComponent(pathname.split('?')[0]);
  const target = filePart ? path.resolve(path.dirname(from), filePart) : from;
  if (!inside(root, target)) throw new Error(`Link escapes published root: ${href}`);
  return { target, fragment: fragment && decodeURIComponent(fragment) };
}

// GitHub heading anchors retain hyphens and replace each space after stripping punctuation.
function markdownIds(source) {
  const ids = new Set([...source.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]));
  markdown.walkTokens(markdown.lexer(source), token => {
    if (token.type !== 'heading') return;
    const slug = token.text.toLowerCase().replace(/<[^>]*>/g, '')
      .replace(/[\p{P}\p{S}]/gu, char => /[-_]/.test(char) ? char : '').replace(/\s/g, '-');
    let id = slug, suffix = 0;
    while (ids.has(id)) id = `${slug}-${++suffix}`;
    ids.add(id);
  });
  return ids;
}

function checkLink(root, from, href, ids) {
  if (!local(href)) return;
  checked++;
  try {
    const { target, fragment } = resolveLink(root, from, href);
    if (!fs.existsSync(target)) throw new Error(`Missing file: ${href}`);
    if (fs.statSync(target).isDirectory()) {
      if (path.extname(from) === '.html' && !fs.existsSync(path.join(target, 'index.html'))) {
        throw new Error(`Directory has no index.html for static hosting: ${href}`);
      }
      return;
    }
    if (!fragment) return;
    const targetIds = target === from && ids ? ids
      : path.extname(target) === '.html'
        ? new Set([...read(target).matchAll(/\bid="([^"]+)"/g)].map(match => match[1]))
        : markdownIds(read(target));
    if (!targetIds.has(fragment)) throw new Error(`Missing anchor: ${href}`);
  } catch (error) {
    errors.push(`${path.relative(root, from)}: ${error.message}`);
  }
}

function checkSources() {
  for (const name of sourceDocuments) {
    const file = path.join(repo, name), source = read(file), ids = markdownIds(source);
    markdown.walkTokens(markdown.lexer(source), token => {
      if (token.type === 'link' || token.type === 'image') checkLink(repo, file, token.href, ids);
      if (token.type === 'image' && !token.text.trim()) errors.push(`${name}: Image needs alternative text`);
    });
  }
}

function checkHtml(name) {
  const file = path.join(site, name);
  const html = read(file).replace(/<script\b[^>]*>[\s\S]*?<\/script>/g, '');
  const allIds = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  const ids = new Set(allIds);
  if (allIds.length !== ids.size) errors.push(`${name}: Duplicate HTML IDs`);
  for (const [, href] of html.matchAll(/\b(?:href|src)="([^"]+)"/g)) checkLink(site, file, href, ids);
  for (const [img] of html.matchAll(/<img\b[^>]*>/g)) {
    // The empty dialog image receives its source and alternative text when opened.
    if (img.includes('id="viewer-image"')) continue;
    if (!/\balt="[^"]+"/.test(img)) errors.push(`${name}: Image needs alternative text`);
    if (!/\bwidth="\d+"/.test(img) || !/\bheight="\d+"/.test(img)) errors.push(`${name}: Image needs dimensions`);
  }
}

function copyFile(relative) {
  const target = path.join(site, relative);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(path.join(repo, relative), target);
}

function copyTree(relative, extensions) {
  for (const entry of fs.readdirSync(path.join(repo, relative), { withFileTypes: true })) {
    if (entry.name.startsWith('.') || ['node_modules', '__pycache__'].includes(entry.name)) continue;
    const name = path.join(relative, entry.name);
    if (entry.isDirectory()) copyTree(name, extensions);
    else if (entry.isFile() && (extensions.has(path.extname(entry.name)) || entry.name === 'guide-lines')) copyFile(name);
  }
}

if (!process.argv.includes('--check')) {
  // Only replace the generated directory at this exact checkout-local location.
  if (path.dirname(site) !== repo || path.basename(site) !== '_site' ||
      (fs.existsSync(site) && fs.lstatSync(site).isSymbolicLink())) {
    throw new Error('Refusing to replace an unexpected output directory');
  }
  fs.rmSync(site, { recursive: true, force: true });
  fs.mkdirSync(site);
  copyTree('desing', new Set(['.md', '.html', '.css', '.mjs', '.json', '.png', '.svg']));
  for (const skill of ['spring-boot-ai', 'spring-boot-vsa', 'angular-vertical-slice']) {
    copyTree(skill, new Set(['.md', '.py', '.tmpl']));
  }
  for (const name of ['README.md', 'install.ps1', 'install.sh', '.github/workflows/pages.yml']) copyFile(name);
  const original = path.join(repo, 'desing/guide-lines.html');
  const index = read(original).replace(/\bhref="([^"]+)"/g, (match, href) => {
    if (!local(href) || href.startsWith('#')) return match;
    const { target } = resolveLink(repo, original, href);
    const suffix = href.match(/[?#].*$/)?.[0] || '';
    return `href="${path.relative(repo, target).split(path.sep).join('/')}${suffix}"`;
  });
  fs.writeFileSync(path.join(site, 'index.html'), index);
  fs.writeFileSync(path.join(site, '.nojekyll'), '');
}

checkSources();
checkHtml('index.html');
checkHtml('desing/guide-lines.html');
if (errors.length) throw new Error(`Handbook validation failed:\n${errors.join('\n')}`);
console.log(`Checked ${checked} local file/anchor references and image metadata. GitHub Pages output: _site/`);
