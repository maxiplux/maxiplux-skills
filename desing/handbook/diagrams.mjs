import fs from 'node:fs';
import path from 'node:path';

const esc = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const text = (x, y, value, cls = 'body') => `<text x="${x}" y="${y}" class="${cls}">${esc(value)}</text>`;
const lines = (x, y, values, cls = 'body', gap = 28) => values.map((v, i) => text(x, y + i * gap, v, cls)).join('');
const rect = (x, y, w, h, fill = '#ffffff', stroke = '#c2d3ed', r = 14) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}" stroke-width="2"/>`;
const arrow = (d, label = '', x = 0, y = 0) => `<path d="${d}" fill="none" stroke="#245bd6" stroke-width="3" marker-end="url(#arrow)"/>${label ? text(x, y, label, 'small') : ''}`;
const card = (x, y, w, h, label, title, content, blue = false) => rect(x,y,w,h,blue?'#e7f0ff':'#ffffff',blue?'#245bd6':'#c2d3ed') + text(x+22,y+31,label,'label') + text(x+22,y+68,title,'heading') + lines(x+22,y+105,content);
const frame = (title, description, h, body) => `<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="${h}" viewBox="0 0 1400 ${h}" role="img" aria-labelledby="title description">
<title id="title">${esc(title)}</title><desc id="description">${esc(description)}</desc>
<defs><style>text{font-family:Segoe UI,Arial,sans-serif;fill:#132f55}.title{font-size:36px;font-weight:750}.heading{font-size:24px;font-weight:700}.body{font-size:21px}.small{font-size:18px}.label{font-size:16px;font-weight:700;letter-spacing:1.1px}.white{fill:#ffffff}.mono{font-family:Consolas,monospace;font-size:20px}.note{font-size:20px;font-weight:600}</style><marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9Z" fill="#245bd6"/></marker></defs>
${rect(0,0,1400,h,'#f8fbff','#c2d3ed',22)}${text(42,62,title,'title')}${body}
</svg>\n`;

export function renderDiagrams(root) {
  const diagrams = {};
  diagrams['ui-form-lifecycle.svg'] = frame('A form is a conversation, not a collection of inputs.',
    'A worked invoice form with persistent labels, required fields, an inline error, preserved customer value and a focus indicator. Six lifecycle states cover editing, checking, saving, success, failure and uncertain write results. Server validation remains authoritative.', 1050,
    text(42,104,'Example: creating an invoice. Read the details above the state flow before shipping the form.') +
    rect(42,142,625,530) + text(68,185,'Create invoice','heading') + text(68,220,'Fields marked * are required. Amounts are in USD.','small') +
    text(68,268,'Customer *','note') + rect(68,282,570,57,'#f8fbff') + text(88,318,'Acme Ltd') +
    text(68,380,'Amount (USD) *','note') + rect(64,392,578,65,'#f8fbff','#245bd6') + rect(69,397,568,55,'#ffffff','#8b3524',10) + text(88,431,'0.00') +
    text(68,489,'Enter an amount greater than zero.','note') + text(68,520,'The message is associated with the field.','small') +
    rect(68,555,210,61,'#245bd6','#245bd6',10) + text(92,594,'Create invoice','body white') +
    text(305,579,'Specific action label','small') + text(305,606,'Keep other values intact','small') +
    card(706,142,652,250,'BEFORE & DURING INPUT','Make the requirements clear',[
      'Use persistent labels, required indicators and units.',
      'Use an appropriate input type and keyboard.',
      'Allow paste, correction and ordinary navigation.',
      'Do not rely on a placeholder or color alone.'
    ],true) +
    card(706,416,652,256,'WHEN THE PERSON SUBMITS','Help them finish or recover',[
      'Identify errors and help focus the first correction.',
      'Show progress; avoid duplicate submissions.',
      'Keep recoverable input after a failure.',
      'Explain the outcome and the next useful action.'
    ]) +
    text(42,724,'EDIT → CHECK → SAVE · THEN ONE OUTCOME: SUCCESS, FAILURE OR UNKNOWN','label') +
    [
      ['1 · EDIT','Enter values','Labels + help'],['2 · CHECK','Fix fields','Keep input'],['3 · SAVE','Request pending','Show progress'],
      ['4 · SUCCESS','Invoice created','Confirm outcome'],['5 · FAILURE','Recover safely','Explain next step'],['6 · UNKNOWN','Write timed out','Check before retry']
    ].map((v,i)=>rect(42+i*222,749,206,144,i===5?'#e7f0ff':'#ffffff')+text(58+i*222,781,v[0],'label')+text(58+i*222,820,v[1],'small')+text(58+i*222,857,v[2],'small')).join('') +
    rect(42,925,1316,83,'#132f55','#132f55') + text(65,959,'Client checks improve feedback. Server validation enforces the business rules.','heading white') +
    text(65,990,'These are distinct outcomes; a timeout does not prove that a write failed.','small white'));

  diagrams['agent-control-loop.svg'] = frame('The model proposes. The application controls execution.',
    'Context enters a model decision. An answer exits the loop. A requested tool call passes through argument, authorization, tenant and approval checks before execution. The bounded result returns as an observation. Stop conditions and output validation apply throughout.', 1060,
    text(42,104,'Example: investigate an unpaid invoice, then prepare a reminder for review.') +
    rect(42,142,1316,127,'#e7f0ff','#245bd6') + text(64,176,'CONTEXT FOR THIS REQUEST','label') +
    lines(64,213,['User goal + approved instructions + allowed tool schemas + relevant business data',
      'Optional: retrieved policy documents and scoped conversation memory. External text remains data.']) +
    arrow('M525 270 V322') +
    card(42,338,260,235,'1 · GOAL','Investigate', ['Invoice INV-104','Why is it unpaid?','Who is asking?','Which tenant?']) +
    card(338,338,336,235,'2 · MODEL DECISION','Answer or request', ['Tool: getPayments','Argument: invoiceId','Or return an answer','with supporting evidence'],true) +
    card(710,338,306,235,'3 · APPLICATION GATE','Check the request', ['Validate arguments','Authorize + scope data','Enforce allowed tools','Require approval if needed'],true) +
    card(1052,338,306,235,'4 · TOOL EXECUTION','Run bounded work', ['Call application service','Apply timeout / limits','Return data or typed error','Record the outcome']) +
    arrow('M303 450 H326') + arrow('M675 450 H698') + arrow('M1017 450 H1040') +
    rect(42,641,632,169) + text(64,681,'ANSWER PATH','label') +
    lines(64,720,['Validate the result → answer or editable draft.', 'If evidence is missing, ask or explain the limitation.', 'A reminder draft does not authorize sending it.']) +
    arrow('M505 574 V629','answer',525,611) +
    rect(710,641,648,169,'#e7f0ff','#245bd6') + text(732,681,'5 · OBSERVE','label') +
    lines(732,720,['Read the tool result, including failures.', 'Continue only if another allowed step helps the goal.', 'Feed the observation back into the next model call.']) +
    arrow('M1205 574 V629') + arrow('M840 641 V607 H650 V585','tool result → next decision',727,600) +
    rect(42,855,1316,159,'#132f55','#132f55') + text(64,894,'STOP CONDITIONS ARE APPLICATION BEHAVIOR','heading white') +
    lines(64,932,['Goal reached · more user input needed · cancellation · approval denied · unrecoverable error',
      'Step / time / usage limit reached → return a clear outcome instead of continuing indefinitely.'], 'body white'));

  diagrams['architecture-request-flow.svg'] = frame('Trace the request, the data change and the failure.',
    'A save request passes through authentication and authorization, a thin controller, a feature handler and persistence. A short transaction protects the database write. AI extraction is a separate operation outside that transaction. Controller and handler errors reach shared advice; security-layer failures use the security error path. DTOs return to the UI.', 1110,
    text(42,104,'Example: the user reviews an extracted draft, then explicitly creates the invoice.') +
    text(42,160,'SAVE REQUEST · POST /invoices','label') +
    card(42,185,286,239,'1 · SECURITY','Who may act?', ['Authenticate caller','Authorize operation','Scope to the tenant','Do not trust a UI guard']) +
    card(370,185,286,239,'2 · API','Thin controller', ['Validate request shape','Accept a request record','Call the use-case handler','Map status + response']) +
    card(698,185,318,239,'3 · FEATURE','CreateInvoiceHandler', ['Enforce business rules','Own the use case','Define the transaction','Avoid duplicate writes'],true) +
    card(1058,185,300,239,'4 · PERSISTENCE','Repository + DB', ['Bound database queries','Apply constraints','Use schema migrations','Persist feature-owned data']) +
    arrow('M329 304 H358') + arrow('M657 304 H686') + arrow('M1017 304 H1046') +
    rect(698,444,660,55,'#e7f0ff','#245bd6') + text(718,479,'SHORT DB TRANSACTION · keep required writes atomic','note') +
    rect(42,533,1316,139,'#e7f0ff','#245bd6') + text(64,569,'AI EXTRACTION IS A SEPARATE USE CASE','label') +
    lines(64,607,['POST /invoice-drafts → extraction handler → ChatClient → model → validated draft → review UI',
      'Do not keep a database transaction open across the slow model call. Saving uses the request above.']) +
    card(42,710,632,205,'SUCCESS PATH','Return an API response record', [
      'Map from domain/persistence types to the agreed DTO.',
      'Expose the outcome the UI needs, not the JPA entity.',
      'The UI confirms success and refreshes the relevant data.'
    ]) +
    card(710,710,648,205,'FAILURE PATH','Translate once at the correct boundary', [
      'Controller / handler exception → shared advice → ProblemDetail.',
      'Security-filter failures use the configured security response path.',
      'UI maps stable problem types to a useful recovery action.'
    ],true) +
    rect(42,955,1316,111,'#132f55','#132f55') + text(64,993,'VERIFY EACH BOUNDARY','heading white') +
    text(64,1030,'HTTP contract · handler rules · database behavior · provider failures · complete browser task','body white'));

  diagrams['fullstack-handoff.svg'] = frame('One feature. Three kinds of decisions. One contract.',
    'UI UX owns the task and recovery states. AI work owns interpretation and evaluation. Architecture owns contracts, boundaries and persistence. They share a versioned API and acceptance criteria. The example separates draft extraction from invoice creation and verifies one complete journey.', 940,
    text(42,104,'Worked example: paste invoice text → extract → correct the draft → create the invoice.') +
    rect(42,142,1316,103,'#132f55','#132f55') + text(64,180,'AGREE FIRST','label white') +
    text(64,217,'Input + output DTOs · error types · authorization · draft-versus-save behavior · acceptance cases','body white') +
    card(42,290,412,360,'01 · UI / UX & DESIGN','Make the task usable', [
      'Lead: Impeccable for the app',
      'Review: Web Design Guidelines',
      '',
      'Text input → progress → editable draft',
      'Keep input through recoverable errors',
      'Label fields, actions and status',
      'Check keyboard + narrow screens'
    ]) +
    card(494,290,412,360,'02 · AI AGENTS','Bound model behavior', [
      'Guide: spring-boot-ai',
      'Choose a fixed workflow first',
      '',
      'Prompt → model → typed draft',
      'Check missing and invalid fields',
      'Limit retries, time and tool access',
      'Evaluate output with known cases'
    ],true) +
    card(946,290,412,360,'03 · SOFTWARE ARCHITECTURE','Keep ownership clear', [
      'Guide: spring-boot-vsa',
      'Angular: angular-vertical-slice',
      '',
      'Controller → handler → persistence',
      'Keep extraction separate from saving',
      'Preserve DTO and error contracts',
      'Protect writes with a short transaction'
    ]) +
    arrow('M248 246 V278') + arrow('M700 246 V278') + arrow('M1150 246 V278') +
    rect(42,692,1316,195,'#e7f0ff','#245bd6') + text(64,733,'INTEGRATION CHECK · THE SAME DATA MUST WORK ACROSS ALL THREE','heading') +
    lines(64,773,[
      'A missing currency becomes a clear correction, not an invented value or a broken form.',
      'A model timeout preserves the text; a rejected save explains the field or permission problem.',
      'A successful extraction creates a draft. Only the explicit save action creates an invoice.',
      'Review the diff, run focused checks and record which provider/browser paths were actually exercised.'
    ]));

  for (const [name, source] of Object.entries(diagrams)) fs.writeFileSync(path.join(root,'assets',name),source);
  return Object.keys(diagrams);
}
