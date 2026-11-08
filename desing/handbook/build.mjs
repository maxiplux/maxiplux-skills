import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { Marked } from 'marked';
import { chapters } from './chapters.mjs';
import { renderDiagrams } from './diagrams.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const read = name => fs.readFileSync(path.join(here, name), 'utf8');
const escape = text => text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const chapterLinks = new Map();
for (const chapter of chapters) {
  chapterLinks.set(chapter.file, '#' + chapter.id);
  const headings = [...fs.readFileSync(path.join(root,chapter.file),'utf8').matchAll(/^## (.+)$/gm)];
  headings.forEach((match,i)=> {
    const slug = match[1].toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu,'').replace(/\s+/g,'-');
    chapterLinks.set(chapter.file+'#'+slug, '#'+chapter.sections[i]?.[0]);
  });
}
let activeChapter, sectionIndex = 0, code = 0, figure = 0, quizCount = 0;

function renderQuiz(sectionId, item) {
  if (!item) throw new Error(`Add a quiz entry for ${activeChapter.file}#${sectionId}`);
  const quizId = `quiz-${++quizCount}`;
  const feedbackId = `${quizId}-feedback`;
  return `<aside class="section-quiz card bg-base-200 border border-base-300 my-8" data-quiz="${quizId}" data-quiz-correct="${item.correct}"><div class="card-body p-5 sm:p-6"><div class="flex flex-wrap items-center justify-between gap-3"><p class="quiz-kicker">Check your understanding</p><span class="badge badge-outline">Quick quiz</span></div><h4 class="quiz-question" id="${quizId}-question">${escape(item.question)}</h4><div class="quiz-options grid gap-2 mt-3" role="group" aria-labelledby="${quizId}-question">${item.options.map((option, index) => `<button type="button" class="btn quiz-option justify-start text-left h-auto min-h-12 whitespace-normal" data-quiz-answer="${index}" aria-describedby="${feedbackId}" aria-pressed="false">${escape(option)}</button>`).join('')}</div><p class="quiz-feedback mt-3" id="${feedbackId}" role="status" aria-live="polite" aria-atomic="true"></p><p class="quiz-explanation text-sm mt-1 hidden">${escape(item.explanation)}</p></div></aside>`;
}
renderDiagrams(root);
const markdown = new Marked({ gfm: true, renderer: {
  link({href,title,tokens}) {
    const target = chapterLinks.get(href.replace(/^\.\//,'')) || href;
    return `<a href="${escape(target)}"${title?` title="${escape(title)}"`:''}>${this.parser.parseInline(tokens)}</a>`;
  },
  heading({tokens, depth}) {
    const text = this.parser.parseInline(tokens);
    if (depth === 1) return `<h2 id="${activeChapter.id}">${text}</h2>`;
    if (depth === 2) {
      const entry = activeChapter.sections[sectionIndex++];
      if (!entry) throw new Error(`Add a section entry for ${activeChapter.file}: ${text}`);
      return `<h3 id="${entry[0]}" data-section>${text}</h3>`;
    }
    return `<h${Math.min(depth+1,6)}>${text}</h${Math.min(depth+1,6)}>`;
  },
  code({text, lang}) {
    const id = `code-${++code}`;
    const labels = {powershell: 'Terminal · PowerShell / shell', java: 'Java · integration excerpt', tree: 'Illustrative project structure', template: 'Prompt resource · text', text: 'Agent chat · copy and adapt'};
    const label = labels[lang] || 'Code example';
    return `<div class="code-box border border-base-300 rounded-box overflow-hidden my-5 bg-base-200"><div class="flex flex-wrap gap-2 justify-between items-center px-4 py-2 border-b border-base-300"><span class="text-xs font-semibold uppercase tracking-wide">${label}</span><button class="btn btn-sm copy-button" type="button" data-copy="${id}" aria-label="Copy ${label}">Copy</button></div><pre><code translate="no" id="${id}">${escape(text)}</code></pre></div>`;
  },
  image({href, text}) {
    const location = path.resolve(root, href);
    if (!location.startsWith(root + path.sep)) throw new Error('Image must be inside the document folder.');
    const bytes = fs.readFileSync(location);
    let width, height, mime, format;
    if (path.extname(location).toLowerCase() === '.svg') {
      const svg = bytes.toString('utf8');
      const size = svg.match(/<svg\b[^>]*\bviewBox="0 0 (\d+) (\d+)"/);
      if (!size || /<script\b|<foreignObject\b|\bon\w+\s*=|\b(?:href|src)\s*=/i.test(svg)) throw new Error('Expected a static, self-contained SVG with a viewBox.');
      [, width, height] = size;
      mime = 'image/svg+xml'; format = 'SVG';
    } else {
      if (!bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) throw new Error('Expected PNG or SVG illustration.');
      width = bytes.readUInt32BE(16); height = bytes.readUInt32BE(20);
      mime = 'image/png'; format = 'PNG';
    }
    const data = `data:${mime};base64,${bytes.toString('base64')}`;
    return `<figure><button type="button" class="image-preview block w-full cursor-zoom-in" data-open-image="${path.basename(location)}" aria-haspopup="dialog" aria-controls="image-viewer" aria-label="Enlarge illustration ${++figure}: ${escape(text)}"><img src="${data}" width="${width}" height="${height}" alt="${escape(text)}" loading="lazy"></button><figcaption class="figure-hint">${format} · Open to enlarge, inspect the details or save. A text explanation accompanies the visual.</figcaption></figure>`;
  }
}});

const shell = read('shell.html');
function enhance(content) {
  content = content.replace(/<p>(\s*<figure>[\s\S]*?<\/figure>)\s*<\/p>/g, '$1');
  content = content.replaceAll('<table>', '<div class="overflow-x-auto border border-base-300 rounded-box my-6" tabindex="0" role="region" aria-label="Comparison table; scroll horizontally on small screens"><table class="table">').replaceAll('</table>', '</table></div>').replaceAll('<th>', '<th scope="col">');
  content = content.replace(/<code(?![^>]*translate=)/g, '<code translate="no"');
  for (const marker of ['TOOL_PICKER', 'DESIGN_VOCABULARY', 'STATE_PLAYGROUND', 'WORKFLOW_RECIPES']) {
    const match = shell.match(new RegExp(`<!-- PART:${marker} -->([\\s\\S]*?)<!-- END:${marker} -->`));
    if (!match) throw new Error(`Missing partial ${marker}`);
    content = content.replace(`<!-- ${marker} -->`, match[1]);
  }
  return content;
}
let content = chapters.map((chapter, chapterIndex) => {
  activeChapter = chapter; sectionIndex = 0;
  const rendered = enhance(markdown.parse(fs.readFileSync(path.join(root,chapter.file),'utf8')));
  if (sectionIndex !== chapter.sections.length) throw new Error(`Navigation mismatch in ${chapter.file}`);
  const [intro, ...parts] = rendered.split(/(?=<h3 id=")/);
  const sections = parts.map((part, partIndex) => {
    const entry = chapter.sections[partIndex];
    const match = part.match(/^<h3 id="([^"]+)" data-section>([\s\S]*?)<\/h3>/);
    if (!match) throw new Error('Unexpected section markup');
    return `<section class="guide-section py-10 border-t border-base-300" aria-labelledby="${match[1]}">${match[0]}<div class="section-body">${part.slice(match[0].length)}</div>${renderQuiz(entry[0], entry[2])}</section>`;
  }).join('\n');
  const next = chapters[chapterIndex+1];
  return `<section class="chapter" aria-labelledby="${chapter.id}"><header class="chapter-heading"><p class="chapter-number">Part ${chapterIndex+1} / 3</p>${intro}</header>${sections}${next?`<a href="#${next.id}" class="chapter-next no-print">Next Part: ${next.title} →</a>`:''}</section>`;
}).join('\n');
const indexSource = fs.readFileSync(path.join(root,'guide-lines'),'utf8');
const sourceHeading = indexSource.indexOf('## Sources');
if (sourceHeading < 0) throw new Error('Source index must include Sources');
activeChapter = {id:'sources',sections:[]}; sectionIndex = 0;
const sources = enhance(markdown.parse(indexSource.slice(sourceHeading).replace(/^## /,'# ')));
content += `<section class="sources py-10" aria-labelledby="sources">${sources}</section>`;
let detail = 0;
content = content.replace(/<details(?![^>]*\bid=)([^>]*)>/g, (_,attrs)=>`<details id="detail-${++detail}"${attrs}>`);
const nav = chapters.map((chapter,index)=>`<div class="nav-group"><a href="#${chapter.id}" class="nav-chapter"><span class="font-mono text-xs opacity-65">0${index+1}</span> ${chapter.title}</a><div class="nav-sections">${chapter.sections.map(([id,label])=>`<a href="#${id}" class="nav-section">${label}</a>`).join('')}</div></div>`).join('') + '<a href="#sources" class="nav-section mt-5">Sources & Maintenance</a>';
const result = spawnSync(process.execPath, [path.join(here, 'node_modules/@tailwindcss/cli/dist/index.mjs'), '-i', path.join(here, 'styles.css'), '-o', path.join(here, '.compiled.css'), '--minify'], {cwd: here, stdio: 'inherit'});
if (result.status !== 0) throw new Error('Stylesheet compilation failed');
const output = shell.replace(/<!-- PART:[\s\S]*?<!-- END:[^>]+ -->/g, '').replace('<!-- STYLES -->', `<style>${read('.compiled.css')}</style>`).replace('<!-- NAVIGATION -->', nav).replace('<!-- CONTENT -->', content);
if (/<!-- [A-Z_]+ -->/.test(output)) throw new Error('Unresolved build placeholder');
fs.writeFileSync(path.join(root, 'guide-lines.html'), output.trimEnd() + '\n');
console.log(`Built guide-lines.html: ${chapters.length} parts, ${chapters.flatMap(c=>c.sections).length} sections, ${quizCount} quizzes, ${figure} visuals, ${code} copyable examples, ${(Buffer.byteLength(output)/1024/1024).toFixed(1)} MB. All reading assets embedded.`);
