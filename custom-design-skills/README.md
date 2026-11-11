# Custom design skills

Author: max

Coding-agent skills about **design**: judging, fixing and building user interfaces. Each skill is a
self-contained folder (a `SKILL.md` plus optional `references/`, `assets/` and `scripts/`) that can
be installed on its own.

## Skills

| Skill | What it does | Example request |
| --- | --- | --- |
| **[design-principles-review-by-max](./design-principles-review-by-max/SKILL.md)** | Evaluates any web or mobile UI against Rams' 10 principles, Nielsen's 10 heuristics, Shneiderman's 8 golden rules and the W3C WAI accessibility design tips; plans and applies fixes; runs the whole evaluate → fix → re-evaluate workflow. | "Run a design principles review of the checkout flow and tell me what to fix first." |

## Install

From the repository root. The installers find skills in this folder by name.

```bash
bash ./install.sh --project /path/to/my-app --skill design-principles-review-by-max
```

```powershell
.\install.ps1 -Project "C:\code\my-app" -Skill design-principles-review-by-max
```

Use `--personal` / `-Personal` to install for all your projects. To install by hand, copy the whole
skill folder to `<project>/.claude/skills/` (Claude Code) or `<project>/.agents/skills/` (Codex).

With the Skills CLI, from the application project:

```bash
npx skills add /path/to/maxiplux-skills/custom-design-skills --skill design-principles-review-by-max --copy
```

## Adding a design skill

More design skills will live here. So that they never collide with each other or with skills from
other sources:

1. **Name it `<topic>-by-max`**, lowercase with hyphens: for example `design-tokens-by-max`. The
   name must be unique in this repository.
2. **Folder name = frontmatter `name`.** Create `custom-design-skills/<name>/SKILL.md` with:

   ```yaml
   ---
   name: <topic>-by-max
   description: What it does and when to use it, with the phrases a user would say.
   metadata:
     author: max
     version: "1.0.0"
   ---
   ```

3. **Sign what it produces.** Every report, plan or other artifact the skill outputs ends with
   `— <skill-name> · by max`.
4. **Keep `SKILL.md` short** and move detail into `references/`, loaded only when needed.
5. **Register it**: add a row to the table above and to the skills table in the root
   [README](../README.md).
