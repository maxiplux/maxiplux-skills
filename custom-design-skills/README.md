# Custom design skills

Author: max

This folder holds coding-agent skills about **design**: reviewing, fixing and building user
interfaces. A skill is a folder of instructions that a coding agent (Claude Code, Codex) reads when
your request matches it. Installing a skill only copies that folder. It does not change your
application until you ask the agent to do something.

| Skill | What it does |
| --- | --- |
| **[design-principles-review-by-max](./design-principles-review-by-max/SKILL.md)** | Reviews any web or mobile screen against four sets of design principles (Rams, Nielsen, Shneiderman, W3C WAI accessibility tips), then plans and applies the fixes. |

**On this page:** [Quick start](#quick-start) · [Install](#install) · [Use the skill](#use-the-skill) ·
[Read the report](#read-the-report) · [Helper scripts](#helper-scripts) ·
[Troubleshooting](#troubleshooting) · [Add a design skill](#add-a-design-skill)

## Quick start

One line, with no need to clone this repository. Run it **inside the project you want to review**:

```bash
npx skills add maxiplux/maxiplux-skills --skill design-principles-review-by-max --agent claude-code --copy --yes
```

Then open your coding agent in that project and type:

```text
Run a design principles review of the login screen and tell me what to fix first.
```

The rest of this page explains the other ways to install and every option.

## Install

### What you need

| Need | Why | Required? |
| --- | --- | --- |
| Claude Code or Codex | The agent that runs the skill | Yes |
| Node.js **or** `curl` and `bash` | To install with one line, without cloning | For the one-line install |
| A copy of this repository | Only if you install from a clone | No |
| Node.js and [Playwright](https://playwright.dev/) | Only for `capture.mjs`, which opens a web page in a browser to collect evidence | No |
| Python 3 | Only for `contrast.py`, which measures color contrast | No |

Without Node or Python the skill still works. It reviews from your source code and screenshots, and
says in its report what it could not check.

### Option A. One line, without cloning (recommended)

Run the command **inside your application project**. It downloads the skill from GitHub and copies
it into the project. It works the same in a macOS or Linux terminal, Git Bash and Windows
PowerShell. It needs Node.js.

For Claude Code:

```bash
npx skills add maxiplux/maxiplux-skills --skill design-principles-review-by-max --agent claude-code --copy --yes
```

For Codex:

```bash
npx skills add maxiplux/maxiplux-skills --skill design-principles-review-by-max --agent codex --copy --yes
```

For every project on this computer, add `--global`:

```bash
npx skills add maxiplux/maxiplux-skills --skill design-principles-review-by-max --agent claude-code --copy --yes --global
```

You should see:

```text
Installed 1 skill
  ✓ design-principles-review-by-max (copied)
    → ./.claude/skills/design-principles-review-by-max
```

What each part of the command means:

| Part | Meaning |
| --- | --- |
| `npx skills add` | Runs the [Skills CLI](https://github.com/vercel-labs/skills) without installing it. |
| `maxiplux/maxiplux-skills` | The GitHub repository to download the skill from. |
| `--skill design-principles-review-by-max` | The skill to install. Without it, the CLI offers every skill in the repository. |
| `--agent claude-code` | The agent to install for. Use `codex` for Codex. |
| `--copy` | Copies the files into your project. Without it, the CLI creates links. |
| `--yes` | Does not ask questions. |
| `--global` | Installs for all your projects, not only this one. |

The command also creates `skills-lock.json` in your project. It records where the skill came from.
You can commit it or delete it.

**No Node.js?** This line does the same with `curl` and `bash` (macOS, Linux, Git Bash). It
downloads the repository to a temporary folder and runs its installer:

```bash
curl -fsSL https://codeload.github.com/maxiplux/maxiplux-skills/tar.gz/refs/heads/main | tar -xz -C /tmp && bash /tmp/maxiplux-skills-main/install.sh --project . --skill design-principles-review-by-max
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

#### Step 2. Choose where to install

| Scope | Use it when | The skill is copied to |
| --- | --- | --- |
| **Project** | You want the skill in one application | `<your-project>/.claude/skills/design-principles-review-by-max/` |
| **Personal** | You want the skill in every project on this computer | `~/.claude/skills/design-principles-review-by-max/` |

#### Step 3. Run the installer

Pick the one that matches your system.

**macOS, Linux, or Git Bash on Windows**

Install into one project:

```bash
bash ./install.sh --project /path/to/my-app --skill design-principles-review-by-max
```

Install for all your projects:

```bash
bash ./install.sh --personal --skill design-principles-review-by-max
```

You should see:

```text
Installed design-principles-review-by-max -> /path/to/my-app/.claude/skills/design-principles-review-by-max
```

**Windows PowerShell**

Install into one project:

```powershell
.\install.ps1 -Project "C:\code\my-app" -Skill design-principles-review-by-max
```

Install for all your projects:

```powershell
.\install.ps1 -Personal -Skill design-principles-review-by-max
```

**By hand**

Copy the **whole** folder `custom-design-skills/design-principles-review-by-max/` (with its
`references/`, `assets/` and `scripts/` folders) to one of these places:

| Agent | One project | All your projects |
| --- | --- | --- |
| Claude Code | `<project>/.claude/skills/` | `~/.claude/skills/` |
| Codex | `<project>/.agents/skills/` | `~/.agents/skills/` |

#### Installer options

These are the options of `install.sh` and `install.ps1` (Option B).

| `install.sh` | `install.ps1` | What it does |
| --- | --- | --- |
| `--project PATH` | `-Project PATH` | Installs into that project's `.claude/skills/` folder. |
| `--personal` | `-Personal` | Installs into `.claude/skills/` in your home folder, for every project. |
| `--skill NAME` | `-Skill NAME` | Chooses the skill to install. **Required for this skill.** Without it, the installer copies only the two Spring Boot skills. Repeat it to install several (`-Skill a,b` in PowerShell). |
| `--force` | `-Force` | Replaces an installed copy without asking. Without it, the installer asks before it overwrites. |
| `--help` | `-Help` | Shows the usage text. |
| *(neither `--project` nor `--personal`)* | *(neither)* | The installer asks you where to install. |

### Check that it worked

1. Confirm the folder exists and contains `SKILL.md`:

   ```bash
   ls /path/to/my-app/.claude/skills/design-principles-review-by-max
   ```

   Expected: `SKILL.md  assets  references  scripts`

2. Start a **new** agent session in your project (a running session does not see new skills), and
   ask:

   ```text
   Use design-principles-review-by-max. Tell me which modes it has and what each one does.
   Do not change any files.
   ```

   The agent should name three modes: evaluate, remediate and full workflow.

### Update or remove

**Update.** If you used the one-line install, run the same line again. It replaces the installed
copy with the latest version. If you installed from a clone, pull and install again with `--force`:

```bash
git pull
```

```bash
bash ./install.sh --project /path/to/my-app --skill design-principles-review-by-max --force
```

**Remove.** Your application code is not affected. With the Skills CLI, from your project:

```bash
npx skills remove design-principles-review-by-max --yes
```

Or delete the installed folder:

```bash
rm -rf /path/to/my-app/.claude/skills/design-principles-review-by-max
```

## Use the skill

You use the skill by talking to your agent. There are no commands to memorize: describe what you
want, and the agent picks the right mode. You can also name the skill in your request, or in Claude
Code type `/design-principles-review-by-max` followed by your request.

### Tell it four things

The more of these you give, the better the review. The skill asks if something essential is missing.

| Tell it | Example |
| --- | --- |
| **What to review** | "the checkout flow", "`src/app/features/invoices/`", "this screenshot" |
| **Who uses it, and for what** | "an accountant creating an invoice" |
| **The platform** | web, Flutter, iOS, Android |
| **What it can look at** | the source folder, screenshots, a URL, or the command that starts the app |

### The three modes

| Mode | Ask for it when | Changes your code? | What you get |
| --- | --- | --- | --- |
| **Evaluate** | You want to know what is wrong | Never | A scored report with findings |
| **Remediate** | You have a report and want the fixes | Only after you approve the plan | A fix plan, then the fixes, each one re-checked |
| **Full workflow** | You want review and fixes in one go | Only after you approve the plan | A before/after report |

If your request is unclear, the skill runs **Evaluate**, because it is the only mode that cannot
change anything.

#### Evaluate: review a screen

Say:

```text
Run a design principles review of the invoice screen in src/app/features/invoices/.
The user is an accountant who creates and sends invoices. The app runs with `npm start`
on http://localhost:4200/invoices. Do not change any code.
```

What happens:

1. The skill confirms the scope: screens, platform, user and task.
2. It collects evidence from your code, your screenshots and, if the app runs, the live page.
3. It checks the screen against 47 checks that cover all 38 principles.
4. It records each problem as a finding with a location, the evidence, a severity from 0 to 4, and
   a concrete fix.
5. It shows the report: verdict, score, what to fix first, all findings, what works, and what it
   could not check.

#### Remediate: fix what was found

Run this after an evaluation, in the same conversation or with a saved report. Say:

```text
Fix the findings from the design review.
```

What happens:

1. The skill writes a **fix plan**: each change, the findings it closes, the files it touches, the
   risk, and how it will be verified.
2. **It stops and waits for you.** Nothing is changed yet. Answer with one of:

   | Your reply | Result |
   | --- | --- |
   | `Approve all` | Every fix in the plan is applied, in order. |
   | `Approve 1, 2 and 5` | Only those fixes are applied. |
   | `Change: use an undo toast instead of a confirm dialog` | The plan is revised and shown again. |

3. It applies the approved fixes, most severe first, using your project's own framework, components
   and design tokens.
4. It repeats the original check for each fix and marks each finding **closed**, **partly closed**
   or **open**.

Fixes that would change product behavior, legal or pricing text, or an API are listed separately
under "Needs your decision". They are never applied without a clear yes from you.

#### Full workflow: review, fix and verify

Say:

```text
Run the full design review workflow on the signup flow: evaluate it, plan the fixes,
wait for my approval, apply them, and re-evaluate.
```

What happens:

1. **Evaluate**: the "before" report.
2. **Plan**: the fix plan.
3. **Your approval**: the same three replies as in Remediate.
4. **Fix**: the approved fixes are applied and verified.
5. **Re-evaluate**: the same checks are run again.
6. **Final report**: scores before and after, the status of every finding, and what is still open.

The workflow runs once. If findings remain, it lists them and you decide whether to run it again.

### More example requests

| You want | Say |
| --- | --- |
| A review from a picture only | "Review this screenshot against the design principles." (attach the image) |
| Only accessibility | "Check this form against the W3C WAI design tips only." |
| A mobile app | "Run a design principles review of the Flutter settings screen in `lib/settings/`." |
| The report saved as a file | "…and save the report to a file." |
| One section of a long page | "Review only the pricing section of the landing page." |

### Where the files go

The report or plan always appears in the conversation. The skill also writes a file when you ask,
and always in Remediate and Full workflow mode. Files go in your project's existing docs folder, or
in `design-review/` at the project root:

| File | Written by |
| --- | --- |
| `design-review/evaluation-YYYY-MM-DD.md` | Evaluate |
| `design-review/remediation-plan-YYYY-MM-DD.md` | Remediate |
| `design-review/final-report-YYYY-MM-DD.md` | Full workflow |

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
the skill is installed in your project for Claude Code (for Codex the folder is `.agents/skills/`);
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
| The agent does not use the skill | Start a new agent session. Check that `SKILL.md` exists in the installed folder ([Check that it worked](#check-that-it-worked)). Then name the skill in your request: "Use design-principles-review-by-max to…". |
| `Skipping …: no such skill` | The name after `--skill` is misspelled. It must be exactly `design-principles-review-by-max`. |
| `--project requires a PATH` or `--skill requires a NAME` | A value is missing after that option. |
| `npx: command not found` | Node.js is not installed. Install it, or use the `curl` line in [Option A](#option-a-one-line-without-cloning-recommended). |
| The installer copied the Spring Boot skills | `--skill design-principles-review-by-max` was left out. Run the command again with it. |
| `Playwright was not found` | Run `capture.mjs` from a project that has Playwright installed, or install it in that project (`npm install --save-dev playwright`, then `npx playwright install chromium`). Without it, the skill reviews from code and screenshots. |
| PowerShell refuses to run `install.ps1` | Allow scripts for this session, then run it again: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| The review covers too much of a long page | Name the section in your request, or pass `--scope` to `capture.mjs`. |

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
