# Spring Boot Claude Code Skills

Two Claude Code skills for backend Java engineers working on Spring Boot:

| Skill | What it does |
|-------|--------------|
| **spring-boot-ai** | Spring AI patterns: `ChatClient`, structured output (`BeanOutputConverter`), externalized prompt templates, plus production-grade Spring Boot patterns (security, testing, logging, Flyway, Bucket4j). |
| **spring-boot-vsa** | Vertical Slice Architecture enforcement: scaffolding script, JPA templates, conventions for `features/{name}/{api,handlers,model}` packaging. |

Both are standalone — install one or both, personally for all your projects or scoped to a single repo.

## Install (macOS / Linux / Git Bash on Windows)

```bash
# Personal — available in every project on this machine
./install.sh --personal

# Scoped to one project
./install.sh --project /path/to/your/spring-app

# Just one skill
./install.sh --personal --skill spring-boot-vsa
```

## Install (native Windows PowerShell)

```powershell
# Personal
.\install.ps1 -Personal

# Per-project
.\install.ps1 -Project C:\code\my-spring-app

# One skill, force overwrite
.\install.ps1 -Personal -Skill spring-boot-vsa -Force
```

## Install manually

Copy either skill folder into one of:

- `~/.claude/skills/<skill-name>/` — personal (all projects)
- `<project>/.claude/skills/<skill-name>/` — scoped to one project

Claude Code auto-discovers any subdirectory of those paths that contains a `SKILL.md`. No restart needed for new sessions.

## Verify it works

Open Claude Code in any Spring Boot project after installing and try one of:

- *"Scaffold a new `payment` feature slice"* → should trigger **spring-boot-vsa** and offer to run `scripts/create_slice.py`.
- *"How do I parse this LLM JSON response into a Java record?"* → should trigger **spring-boot-ai** and reference `references/structured-output.md`.
- *"What's the convention for externalizing prompts?"* → should reference `references/prompt-templates.md`.

If a skill doesn't trigger, ask Claude `/skills` to list what's loaded.

## Uninstall

```bash
# Personal
rm -rf ~/.claude/skills/spring-boot-ai ~/.claude/skills/spring-boot-vsa

# Per-project
rm -rf <project>/.claude/skills/spring-boot-ai <project>/.claude/skills/spring-boot-vsa
```

```powershell
# Windows personal
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\skills\spring-boot-ai", "$env:USERPROFILE\.claude\skills\spring-boot-vsa"
```

## Layout of this repo

```
.
├── README.md
├── install.sh
├── install.ps1
├── spring-boot-ai/
│   ├── SKILL.md
│   └── references/
│       ├── prompt-templates.md
│       ├── spring-boot-patterns.md
│       └── structured-output.md
└── spring-boot-vsa/
    ├── SKILL.md
    ├── references/      (3 worked examples)
    ├── scripts/         (create_slice.py)
    └── assets/          (14 .java.tmpl templates)
```

Extras
npx skills add https://github.com/mattpocock/skills --skill grill-me
