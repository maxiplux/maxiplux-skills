# Custom design skills

Author: max

This folder holds coding-agent skills about **design**: reviewing, fixing and building user
interfaces. A skill is a folder of instructions that a coding agent reads. These skills work in
**Claude Code**, **Codex** and **Google Antigravity**. Installing a skill only copies that folder.
It does not change your application until you run the skill's command.

| Skill | What it does | Command |
| --- | --- | --- |
| **[design-principles-review-by-max](./design-principles-review-by-max/SKILL.md)** | Reviews any web or mobile screen against four sets of design principles (Rams, Nielsen, Shneiderman, W3C WAI accessibility tips), then plans and applies the fixes. | `/design-principles-review-by-max <mode> [target]` |

**On this page:** [Quick start](#quick-start) · [Install](#install) · [Commands](#commands) ·
[Cookbook](#cookbook-ready-to-copy-commands) · [A typical session](#a-typical-session) ·
[Read the report](#read-the-report) · [Helper scripts](#helper-scripts) ·
[Troubleshooting](#troubleshooting) · [Add a design skill](#add-a-design-skill)

## Quick start

**1. Install.** Run one line **inside the project you want to review**. You do not need to clone
this repository. Pick your agent:

| Agent | Install command |
| --- | --- |
| Claude Code | `npx skills add maxiplux/maxiplux-skills --skill design-principles-review-by-max --agent claude-code --copy --yes` |
| Codex | `npx skills add maxiplux/maxiplux-skills --skill design-principles-review-by-max --agent codex --copy --yes` |
| Antigravity | `npx skills add maxiplux/maxiplux-skills --skill design-principles-review-by-max --agent antigravity --copy --yes` |

**2. Start a new agent session** in that project, so it sees the new skill.

**3. Run the command.** In Claude Code and Antigravity:

```text
/design-principles-review-by-max evaluate src/app/login
```

In Codex, start it with `$` instead of `/`:

```text
$design-principles-review-by-max evaluate src/app/login
```

You get a scored review with the problems to fix first. Nothing in your code changes.

## Install

### What you need

| Need | Why | Required? |
| --- | --- | --- |
| Claude Code, Codex or Antigravity | The agent that runs the skill | Yes |
| Node.js **or** `curl` and `bash` | To install with one line, without cloning | For the one-line install |
| A copy of this repository | Only if you install from a clone | No |
| Node.js and [Playwright](https://playwright.dev/) | Only for `capture.mjs`, which opens a web page in a browser to collect evidence | No |
| Python 3 | Only for `contrast.py`, which measures color contrast | No |

Without Node or Python the skill still works. It reviews from your source code and screenshots, and
says in its report what it could not check.

### Where each agent looks for skills

| Agent | One project | All your projects |
| --- | --- | --- |
| Claude Code | `<project>/.claude/skills/` | `~/.claude/skills/` |
| Codex | `<project>/.agents/skills/` | `~/.agents/skills/` |
| Antigravity | `<project>/.agents/skills/` | `~/.gemini/config/skills/` |

Every install method below copies the folder `design-principles-review-by-max/` into one of these.

### Option A. One line, without cloning (recommended)

Run the command **inside your application project**. It downloads the skill from GitHub and copies
it into the project. It works the same in a macOS or Linux terminal, Git Bash and Windows
PowerShell. It needs Node.js.

```bash
npx skills add maxiplux/maxiplux-skills --skill design-principles-review-by-max --agent claude-code --copy --yes
```

For another agent, change only the `--agent` value:

| Your agent | Use | Installed to |
| --- | --- | --- |
| Claude Code | `--agent claude-code` | `.claude/skills/design-principles-review-by-max/` |
| Codex | `--agent codex` | `.agents/skills/design-principles-review-by-max/` |
| Antigravity | `--agent antigravity` | `.agents/skills/design-principles-review-by-max/` |

For every project on this computer, add `--global`:

```bash
npx skills add maxiplux/maxiplux-skills --skill design-principles-review-by-max --agent antigravity --copy --yes --global
```

You should see:

```text
Installed 1 skill
  ✓ design-principles-review-by-max (copied)
    → ./.agents/skills/design-principles-review-by-max
```

What each part of the command means:

| Part | Meaning |
| --- | --- |
| `npx skills add` | Runs the [Skills CLI](https://github.com/vercel-labs/skills) without installing it. |
| `maxiplux/maxiplux-skills` | The GitHub repository to download the skill from. |
| `--skill design-principles-review-by-max` | The skill to install. Without it, the CLI offers every skill in the repository. |
| `--agent …` | The agent to install for: `claude-code`, `codex` or `antigravity`. |
| `--copy` | Copies the files into your project. Without it, the CLI creates links. |
| `--yes` | Does not ask questions. |
| `--global` | Installs for all your projects, not only this one. |

The command also creates `skills-lock.json` in your project. It records where the skill came from.
You can commit it or delete it.

**No Node.js?** This line does the same with `curl` and `bash` (macOS, Linux, Git Bash). It
downloads the repository to a temporary folder and runs its installer. Change `--agent` as needed:

```bash
curl -fsSL https://codeload.github.com/maxiplux/maxiplux-skills/tar.gz/refs/heads/main | tar -xz -C /tmp && bash /tmp/maxiplux-skills-main/install.sh --project . --skill design-principles-review-by-max --agent claude
```

Now go to [Check that it worked](#check-that-it-worked).

### Option B. From a clone of this repository

Use this when you already have the repository, or when you want the PowerShell installer.

#### Step 1. Get the repository

```bash
git clone https://github.com/maxiplux/maxiplux-skills.git
```

```bash
cd maxiplux-skills
```

Run every command in Option B from this `maxiplux-skills` folder.

#### Step 2. Run the installer

**macOS, Linux, or Git Bash on Windows**

Install into one project, for Claude Code:

```bash
bash ./install.sh --project /path/to/my-app --skill design-principles-review-by-max
```

The same for Antigravity, or for Codex:

```bash
bash ./install.sh --project /path/to/my-app --skill design-principles-review-by-max --agent antigravity
```

```bash
bash ./install.sh --project /path/to/my-app --skill design-principles-review-by-max --agent codex
```

Install for all your projects:

```bash
bash ./install.sh --personal --skill design-principles-review-by-max --agent antigravity
```

You should see:

```text
Installed design-principles-review-by-max -> /path/to/my-app/.agents/skills/design-principles-review-by-max

Done. Start a new Antigravity session in the project and try:
  - /design-principles-review-by-max help
```

**Windows PowerShell**

```powershell
.\install.ps1 -Project "C:\code\my-app" -Skill design-principles-review-by-max
```

```powershell
.\install.ps1 -Project "C:\code\my-app" -Skill design-principles-review-by-max -Agent antigravity
```

```powershell
.\install.ps1 -Personal -Skill design-principles-review-by-max -Agent codex
```

**By hand**

Copy the **whole** folder `custom-design-skills/design-principles-review-by-max/` (with its
`references/`, `assets/` and `scripts/` folders) into the folder for your agent in
[Where each agent looks for skills](#where-each-agent-looks-for-skills).

#### Installer options

| `install.sh` | `install.ps1` | What it does |
| --- | --- | --- |
| `--project PATH` | `-Project PATH` | Installs into that project. |
| `--personal` | `-Personal` | Installs for every project, in your home folder. |
| `--agent NAME` | `-Agent NAME` | The agent: `claude` (default), `codex` or `antigravity`. It decides the folder (see [the table](#where-each-agent-looks-for-skills)). |
| `--skill NAME` | `-Skill NAME` | The skill to install. **Required for this skill.** Without it, the installer copies only the two Spring Boot skills. Repeat it to install several (`-Skill a,b` in PowerShell). |
| `--force` | `-Force` | Replaces an installed copy without asking. Without it, the installer asks before it overwrites. |
| `--help` | `-Help` | Shows the usage text. |
| *(neither `--project` nor `--personal`)* | *(neither)* | The installer asks you where to install. |

### Check that it worked

1. Confirm the folder exists and contains `SKILL.md` (for Codex and Antigravity the folder is
   `.agents/skills/`):

   ```bash
   ls /path/to/my-app/.claude/skills/design-principles-review-by-max
   ```

   Expected: `SKILL.md  assets  references  scripts`

2. Start a **new** agent session in your project (a running session does not see new skills), and
   run:

   ```text
   /design-principles-review-by-max help
   ```

   In Codex: `$design-principles-review-by-max help`. You should see the usage text with the modes
   and examples. `help` never changes anything.

### Update or remove

**Update.** If you used the one-line install, run the same line again. It replaces the installed
copy with the latest version. If you installed from a clone, pull and install again with `--force`:

```bash
git pull
```

```bash
bash ./install.sh --project /path/to/my-app --skill design-principles-review-by-max --agent antigravity --force
```

**Remove.** Your application code is not affected. With the Skills CLI, from your project:

```bash
npx skills remove design-principles-review-by-max --yes
```

Or delete the installed folder:

```bash
rm -rf /path/to/my-app/.claude/skills/design-principles-review-by-max
```

## Commands

You run the skill with **one command**, followed by a **mode**, then **what to review**:

```text
/design-principles-review-by-max <mode> [target] [focus words]
```

| Mode | Also accepted | What it does | Changes your code? |
| --- | --- | --- | --- |
| `evaluate` | `review`, `audit` | Reviews the target and gives a scored report with findings. | **Never** |
| `remediate` | `fix` | Writes a fix plan from a review, **waits for your approval**, applies the fixes and re-checks each one. | Only after you approve |
| `workflow` | `full` | Evaluate, plan, your approval, fix, then evaluate again and compare. | Only after you approve |
| `help` | *(no mode)* | Shows the usage and examples. | Never |

Anything else as the mode (a typo, for example) only shows the help text. The skill never guesses a
mode, because a wrong guess could change code.

### How to run it in each agent

| Agent | Type | Starts by itself from a plain request? |
| --- | --- | --- |
| Claude Code | `/design-principles-review-by-max evaluate src/app/login` | **No.** It runs only when you type the command. |
| Antigravity | `/design-principles-review-by-max evaluate src/app/login` | Yes, it can. Use the command to be sure it runs. |
| Codex | `$design-principles-review-by-max evaluate src/app/login` | Yes, it can. Use the command to be sure it runs. |

In Claude Code, type `/design` and pick the skill from the menu; the menu shows the hint
`[evaluate|remediate|workflow|help] [target]`. The skill is set to run only from its command there,
so an unrelated request such as "fix this button" never starts a full design review. Codex and
Antigravity have no setting for that, so they may also start it when a request clearly asks for a
design review.

### The target: what to review

Everything after the mode says what to review. Use any of these, alone or together:

| Target | Example |
| --- | --- |
| A folder | `src/app/features/invoices/` |
| A file | `src/components/CheckoutForm.tsx` |
| A running app | `http://localhost:4200/invoices` |
| A deployed page | `https://staging.example.com/pricing` |
| A screen or flow, in words | `"checkout flow"`, `signup from landing page to dashboard` |
| Pictures | screenshots or a design export attached to your message |
| A saved report (remediate) | `design-review/evaluation-2026-11-11.md` |

You can add context in plain words after the target: who the user is, how to start the app, a test
login. The more the agent knows, the less it has to guess.

If you leave the target out, `evaluate` and `workflow` ask you what to review. `remediate` uses the
latest review in the conversation, or the newest file in `design-review/`.

### Focus words: narrow the review

Add these anywhere after the mode.

| Focus words | Effect |
| --- | --- |
| `only accessibility` (or `only a11y`, `only wai`) | Checks accessibility only (the W3C WAI tips). |
| `only rams`, `only nielsen`, `only shneiderman` | Checks one set of principles only. |
| `mobile` | Web pages: checks the phone width (320 px) only. |
| `desktop` | Web pages: checks the desktop width (1280 px) only. |
| `quick` | A short review: verdict and the top five problems. |
| `only severity 3`, `only severity 4` | With `remediate`: plans fixes only for problems that serious or worse. |

## Cookbook: ready-to-copy commands

Copy a command, change the path or URL, and run it. The examples use the `/` form. In Codex,
replace the first `/` with `$`.

### Review something

Review a feature folder:

```text
/design-principles-review-by-max evaluate src/app/features/invoices
```

Review one component file:

```text
/design-principles-review-by-max evaluate src/components/CheckoutForm.tsx
```

Review a page while the app is running. The agent opens it in a browser, takes screenshots, checks
the keyboard order and measures colors:

```text
/design-principles-review-by-max evaluate http://localhost:4200/invoices
```

Review a deployed page you have no code for:

```text
/design-principles-review-by-max evaluate https://staging.example.com/pricing
```

Review a single static HTML file:

```text
/design-principles-review-by-max evaluate public/landing.html
```

Review from screenshots or a design export (attach the images to the same message):

```text
/design-principles-review-by-max evaluate the attached screenshots of the onboarding screens
```

Review a whole flow across several screens:

```text
/design-principles-review-by-max evaluate the signup flow: landing page, sign-up form, email check, first dashboard
```

Review a mobile app screen:

```text
/design-principles-review-by-max evaluate lib/settings/ (Flutter settings screen)
```

```text
/design-principles-review-by-max evaluate ios/App/Views/ProfileView.swift (SwiftUI)
```

```text
/design-principles-review-by-max evaluate app/src/main/java/com/acme/cart/CartScreen.kt (Jetpack Compose)
```

Review one section of a long page:

```text
/design-principles-review-by-max evaluate http://localhost:3000 only the pricing section
```

### Give it context

Say who uses the screen and what they are trying to do. Every check is judged against that task:

```text
/design-principles-review-by-max evaluate src/app/features/invoices. The user is an accountant who creates and sends 20 invoices a day.
```

Tell it how to start the app, so it can review the live page:

```text
/design-principles-review-by-max evaluate the invoices page. Start the app with `npm start`; it runs on http://localhost:4200/invoices.
```

Give it a test login for a page behind sign-in. Use a test account, never a real one:

```text
/design-principles-review-by-max evaluate http://localhost:3000/account. Sign in with test@example.com / test-password first.
```

Name the screen sizes that matter:

```text
/design-principles-review-by-max evaluate http://localhost:3000/checkout. Most of our customers use phones.
```

### Narrow the review

Accessibility only:

```text
/design-principles-review-by-max evaluate src/app/login only accessibility
```

One set of principles only:

```text
/design-principles-review-by-max evaluate src/app/dashboard only nielsen
```

Phone width only:

```text
/design-principles-review-by-max evaluate http://localhost:3000/checkout mobile
```

A quick look before a demo: verdict and the top five problems:

```text
/design-principles-review-by-max evaluate src/app/onboarding quick
```

Combine them:

```text
/design-principles-review-by-max evaluate http://localhost:3000/signup only accessibility mobile quick
```

### Fix what was found

Plan fixes for the review you just ran:

```text
/design-principles-review-by-max remediate
```

Plan fixes from a review saved earlier:

```text
/design-principles-review-by-max remediate design-review/evaluation-2026-11-11.md
```

Plan fixes for serious problems only (severity 3 and 4):

```text
/design-principles-review-by-max remediate only severity 3
```

The plan lists numbered changes and **stops**. Nothing changes until you reply with one of these:

| Reply | Result |
| --- | --- |
| `Approve all` | Every fix in the plan is applied, in order. |
| `Approve 1, 2 and 5` | Only those fixes are applied. |
| `Change: use an undo message instead of a confirm dialog for fix 3` | The plan is revised and shown again. |
| `Stop` | Nothing is applied. The plan stays in `design-review/` for later. |

Fixes that would change product behavior, legal or pricing text, or an API are listed separately
under "Needs your decision". They are never applied without a clear yes from you.

### Review, fix and check in one go

One screen, from start to finish:

```text
/design-principles-review-by-max workflow src/app/features/invoices
```

A flow before a release, focused on phones:

```text
/design-principles-review-by-max workflow "checkout flow" mobile. Start the app with `npm run dev`.
```

The workflow stops once, after the plan, for your approval. At the end it reports the score before
and after, and what is still open.

### Compare after your own changes

Fixed some things yourself? Run evaluate again on the same target. Then ask for the comparison:

```text
/design-principles-review-by-max evaluate src/app/features/invoices. Compare with design-review/evaluation-2026-11-11.md.
```

### Get help

```text
/design-principles-review-by-max help
```

```text
/design-principles-review-by-max
```

Both show the usage and examples. A mistyped mode shows `Unknown mode "<word>".` and then the same
help.

## A typical session

A short example from start to finish, on a sign-in page. You type the lines that start with `/` or
a reply. The agent's answers are shortened, and the scores are an example: yours depend on your
page and on the evidence the agent can see.

**1. Review.**

```text
/design-principles-review-by-max evaluate src/login/index.html. The user is a returning customer signing in.
```

```text
Verdict: Needs work · Overall score 58/100 · 34 of 38 principles assessed · 6 findings

Fix first
1. F-01 · "Sign in" is a clickable <div> (severity 4): keyboard and screen-reader users cannot sign in.
2. F-02 · Fields labelled only by placeholders (severity 3): the label disappears while typing.
3. F-03 · Focus outline removed (severity 3): keyboard users cannot see where they are.
4. F-04 · "Forgot your password?" hint at 2.32:1 contrast (severity 3): hard to read.
…
— design-principles-review-by-max · by max
```

**2. Plan the fixes.**

```text
/design-principles-review-by-max remediate
```

```text
Remediation plan · Status: Awaiting approval: nothing has been changed yet

| # | Change                                              | Closes      | Severity |
| 1 | Replace the <div> with <button type="submit"> in a <form> | F-01   | 4 |
| 2 | Add visible <label for> to email and password       | F-02        | 3 |
| 3 | Restore a visible focus style                       | F-03        | 3 |
| 4 | Darken the hint text to #595959                     | F-04        | 3 |

Reply: Approve all · Approve some (list numbers) · Change (say what)
— design-principles-review-by-max · by max
```

**3. Approve.**

```text
Approve 1, 2 and 3
```

```text
| # | Status  | Findings closed | Verification                                   |
| 1 | Applied | F-01            | Tab reaches the button; Enter submits the form  |
| 2 | Applied | F-02            | Both fields have a label tied to the input      |
| 3 | Applied | F-03            | Focus ring visible on every control             |

Still open: F-04 (not approved), F-05, F-06
— design-principles-review-by-max · by max
```

**4. Check again.**

```text
/design-principles-review-by-max evaluate src/login/index.html. Compare with the previous review.
```

```text
Verdict: Sound, with issues to fix · Overall 81/100 (was 58, +23)
F-01, F-02, F-03 closed · F-04, F-05, F-06 open
— design-principles-review-by-max · by max
```

Or do steps 1 to 4 with one command: `/design-principles-review-by-max workflow src/login/index.html`.

## Tips for good results

- **Say who the user is and what they are doing.** "An accountant creating an invoice" gives a far
  better review than "the invoice page".
- **Give it what it cannot find.** The command that starts the app, the port, a test login.
- **Let it see the running app.** A review from code alone cannot check real colors, keyboard focus
  or how the page reflows on a phone. The report says what it could not check.
- **Review one flow at a time.** A whole app in one run gives a long, shallow report.
- **Scope long pages.** Name the section, or use `quick` for a first pass.
- **Keep the report file.** Re-running on the same target with the same evidence makes the scores
  comparable, so you can see progress.
- **Start with `evaluate`.** It never changes code. Use `remediate` once you agree with the
  findings.

## Where the files go

The report or plan always appears in the conversation. The skill also writes a file when you ask,
and always in `remediate` and `workflow`. Files go in your project's existing docs folder, or in
`design-review/` at the project root:

| File | Written by |
| --- | --- |
| `design-review/evaluation-YYYY-MM-DD.md` | `evaluate` (when asked) and `workflow` |
| `design-review/remediation-plan-YYYY-MM-DD.md` | `remediate` and `workflow` |
| `design-review/final-report-YYYY-MM-DD.md` | `workflow` |

Every report and plan ends with this signature:

```text
— design-principles-review-by-max · by max
```

## Read the report

**Verdict and score.** The score runs from 0 to 100, with one score for each of the four sets of
principles and one overall. It summarizes the findings and is meant for comparing two runs on the
same screen.

| Overall score | Verdict |
| --- | --- |
| 90–100 | Strong |
| 75–89 | Sound, with issues to fix |
| 50–74 | Needs work |
| below 50 | Poor |

One serious problem limits the verdict whatever the score: an open severity-3 finding caps it at
"Sound, with issues to fix", and an open severity-4 finding caps it at "Needs work".

**Severity.** Every finding has one:

| Severity | Meaning | What to do |
| --- | --- | --- |
| 4 | Catastrophe: a task cannot be finished, or data or money can be lost | Fix before release |
| 3 | Major: people get stuck or lose work | High priority |
| 2 | Minor: people are slowed down | Low priority |
| 1 | Cosmetic | Fix if time allows |
| 0 | Not a problem | Nothing |

**Coverage.** The report says how many of the 38 principles were checked. A check is **not
assessed** when the skill had no way to see it, for example keyboard behavior when it only had a
screenshot. A high score with low coverage is not a high score.

**Finding codes.** `R1`–`R10` are Rams' principles, `N1`–`N10` Nielsen's heuristics, `S1`–`S8`
Shneiderman's rules, and `W1`–`W10` the W3C WAI tips. The
[references folder](./design-principles-review-by-max/references/) explains each one.

**Accessibility.** The W3C WAI tips are an introduction. A good result here is not a WCAG
conformance audit.

## Helper scripts

The agent runs these for you during a review. You can also run them yourself. The examples assume
the skill is installed in your project for Claude Code (for Codex and Antigravity the folder is
`.agents/skills/`);
from a clone of this repository, use `custom-design-skills/design-principles-review-by-max/scripts/`
instead.

### `capture.mjs`: collect evidence from a running web page

Opens a page in a browser at phone and desktop width and records screenshots, the keyboard focus
order, and every text color with its background. It needs Node.js and Playwright, and it installs
nothing.

```bash
node .claude/skills/design-principles-review-by-max/scripts/capture.mjs <url> [out-dir] [options]
```

| Argument | Default | What it does |
| --- | --- | --- |
| `<url>` | required | The page to open: `http://localhost:4200/invoices`, or `file:///path/page.html` for a local file. |
| `[out-dir]` | `evidence` | The folder for the results. Use a temporary folder, not your source tree. |
| `--scope <selector>` | whole page | Limits the review to one element, for example `--scope "#checkout-form"`. Use it on long pages. |
| `--widths <list>` | `320,1280` | Viewport widths in CSS pixels, separated by commas. |
| `--max-stops <n>` | `150` | The maximum number of keyboard stops to record. |

Examples:

```bash
node .claude/skills/design-principles-review-by-max/scripts/capture.mjs http://localhost:4200/invoices /tmp/evidence
```

```bash
node .claude/skills/design-principles-review-by-max/scripts/capture.mjs http://localhost:4200/checkout /tmp/evidence --scope "#checkout-form" --widths 320,768,1280
```

The output folder then contains:

| File | Content |
| --- | --- |
| `320-top.png`, `1280-top.png` | A screenshot of the top of the page at each width |
| `320-scope.png`, `1280-scope.png` | With `--scope` only: a screenshot of that element |
| `report.json` | For each width: horizontal overflow, the focus order and whether each control shows focus, and the text color pairs. Once: page title, language, headings, landmarks, inputs without labels, images without text alternatives. |

Exit status: `0` done, `2` wrong usage or Playwright not found.

### `contrast.py`: measure color contrast

Needs Python 3 and nothing else. It has two forms.

**One pair of colors** (text color first, then background):

```bash
python3 .claude/skills/design-principles-review-by-max/scripts/contrast.py '#777' '#fff'
```

```text
Contrast ratio: 4.48:1  (#777 on #fff)
  FAIL  AA  normal text (4.5:1)
  PASS  AA  large text (3:1)
  PASS  AA  UI components and graphics (3:1)
  FAIL  AAA normal text (7:1)
  FAIL  AAA large text (4.5:1)
```

Colors can be written as `#rgb`, `#rrggbb`, `#rrggbbaa`, `rgb(r, g, b)` or `rgba(r, g, b, a)`. Put
them in quotes.

**Every pair captured by `capture.mjs`:**

```bash
python3 .claude/skills/design-principles-review-by-max/scripts/contrast.py --report /tmp/evidence/report.json
```

It lists each text color pair that fails WCAG level AA, with the text it was found on.

| Option | What it does |
| --- | --- |
| `--min RATIO` | With a color pair: exits with status `1` when the ratio is below `RATIO`. Useful in a script or CI check, for example `--min 4.5`. |
| `--report PATH` | Checks every pair in a `report.json`. Exits with status `1` when any text pair fails AA. |

Exit status: `0` passed, `1` below the required ratio, `2` wrong usage or a color it cannot read.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| The command is not in the `/` menu, or the agent says it does not know it | Start a **new** agent session in the project. Check that `SKILL.md` is in the right folder for your agent ([table](#where-each-agent-looks-for-skills)). |
| Antigravity does not see the skill | Antigravity reads `.agents/skills/`, not `.claude/skills/`. Install with `--agent antigravity`, then reload the window. |
| Codex does not see the skill | Codex reads `.agents/skills/`. Install with `--agent codex`, and type `$design-principles-review-by-max`, with `$`. |
| Claude Code: a plain request like "review this screen" does not use the skill | This is on purpose: in Claude Code the skill runs only from its command. Type `/design-principles-review-by-max evaluate …`. |
| It shows the help text instead of reviewing | The first word after the command must be a mode: `evaluate`, `remediate`, `workflow` (or `review`, `audit`, `fix`, `full`). |
| `remediate` says there is no review to work from | Run `evaluate` first, or give the path of a saved report: `/design-principles-review-by-max remediate design-review/evaluation-2026-11-11.md`. |
| `Skipping …: no such skill` | The name after `--skill` is misspelled. It must be exactly `design-principles-review-by-max`. |
| `Unknown agent` | `--agent` takes `claude`, `codex` or `antigravity` in the installers, and `claude-code`, `codex` or `antigravity` in `npx skills add`. |
| `--project requires a PATH`, `--skill requires a NAME` or `--agent requires a NAME` | A value is missing after that option. |
| The installer copied the Spring Boot skills | `--skill design-principles-review-by-max` was left out. Run the command again with it. |
| `npx: command not found` | Node.js is not installed. Install it, or use the `curl` line in [Option A](#option-a-one-line-without-cloning-recommended). |
| `Playwright was not found` | Run `capture.mjs` from a project that has Playwright installed, or install it in that project (`npm install --save-dev playwright`, then `npx playwright install chromium`). Without it, the skill reviews from code and screenshots. |
| PowerShell refuses to run `install.ps1` | Allow scripts for this session, then run it again: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| The review covers too much of a long page | Name the section in the command, add `quick`, or pass `--scope` to `capture.mjs`. |

## Add a design skill

More design skills will live in this folder. These rules keep their names from colliding with each
other and with skills from other sources:

1. **Name it `<topic>-by-max`**, in lowercase with hyphens, for example `design-tokens-by-max`. The
   name must be unique in this repository.
2. **Use the same name for the folder and the frontmatter.** Create
   `custom-design-skills/<name>/SKILL.md` that starts with:

   ```yaml
   ---
   name: <topic>-by-max
   description: What it does and when to use it, with the phrases a user would say.
   metadata:
     author: max
     version: "1.0.0"
   ---
   ```

3. **Sign what it produces.** Every report, plan or other output of the skill ends with
   `— <skill-name> · by max`.
4. **Keep `SKILL.md` short.** Move detail into `references/`, which the agent loads only when it
   needs it.
5. **Register it.** Add a row to the table at the top of this page and to the skills table in the
   root [README](../README.md). The installers find any skill in this folder by its name, so they
   need no change.
