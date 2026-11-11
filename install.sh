#!/usr/bin/env bash
#
# Install the Claude Code skills in this repository.
# Default: spring-boot-ai and spring-boot-vsa. Other skills are installed by name.
#
#   ./install.sh --personal                    # ~/.claude/skills/<skill>/
#   ./install.sh --project /path/to/proj       # <proj>/.claude/skills/<skill>/
#   ./install.sh --skill spring-boot-vsa --personal
#   ./install.sh --skill design-principles-review-by-max --project /path/to/proj
#   ./install.sh --skill design-principles-review-by-max --agent antigravity --project /path/to/proj
#   ./install.sh --personal --force            # overwrite without asking
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALL_SKILLS=(spring-boot-ai spring-boot-vsa)
# Folders that hold skills: the repository root and each skill collection.
SKILL_ROOTS=("${SCRIPT_DIR}" "${SCRIPT_DIR}/custom-design-skills")

scope=""        # "personal" | "project"
project_path="" # only used when scope=project
skills=()       # subset of ALL_SKILLS
force=0
agent="claude"  # claude | codex | antigravity

usage() {
  cat <<EOF
Install the Claude Code skills in this repository.

Usage:
  $0 --personal [--skill NAME] [--agent AGENT] [--force]
  $0 --project PATH [--skill NAME] [--agent AGENT] [--force]
  $0                    # interactive

Options:
  --personal            Install for all your projects (folder depends on --agent).
  --project PATH        Install into one project (folder depends on --agent).
  --agent AGENT         The coding agent: claude (default), codex or antigravity.
                          claude       PATH/.claude/skills/   or  ~/.claude/skills/
                          codex        PATH/.agents/skills/   or  ~/.agents/skills/
                          antigravity  PATH/.agents/skills/   or  ~/.gemini/config/skills/
  --skill NAME          Only install the named skill. Repeat for multiple.
                        Default: spring-boot-ai and spring-boot-vsa.
                        Also available: angular-vertical-slice,
                        design-principles-review-by-max.
  --force               Overwrite existing target dirs without prompting.
  -h, --help            Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --personal)        scope="personal"; shift ;;
    --project)
      if [[ $# -lt 2 || "$2" == --* ]]; then
        echo "--project requires a PATH, e.g. --project /path/to/my-app" >&2; exit 1
      fi
      scope="project"; project_path="$2"; shift 2 ;;
    --skill)
      if [[ $# -lt 2 || "$2" == --* ]]; then
        echo "--skill requires a NAME, e.g. --skill design-principles-review-by-max" >&2; exit 1
      fi
      skills+=("$2"); shift 2 ;;
    --agent)
      if [[ $# -lt 2 || "$2" == --* ]]; then
        echo "--agent requires a NAME: claude, codex or antigravity" >&2; exit 1
      fi
      agent="$2"; shift 2 ;;
    --force)           force=1; shift ;;
    -h|--help)         usage; exit 0 ;;
    *)                 echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$scope" ]]; then
  echo "Where should the skills be installed?"
  select choice in "Personal (all projects)" "This/another project"; do
    case "$REPLY" in
      1) scope="personal"; break ;;
      2) scope="project"; break ;;
    esac
  done
fi

if [[ "$scope" == "project" && -z "$project_path" ]]; then
  read -r -p "Project path [.]: " project_path
  project_path="${project_path:-.}"
fi

case "$agent" in
  claude)      project_dir=".claude/skills";  personal_dir="${HOME}/.claude/skills" ;;
  codex)       project_dir=".agents/skills";  personal_dir="${HOME}/.agents/skills" ;;
  antigravity) project_dir=".agents/skills";  personal_dir="${HOME}/.gemini/config/skills" ;;
  *) echo "Unknown agent '$agent'. Use claude, codex or antigravity." >&2; exit 1 ;;
esac

case "$scope" in
  personal) target_root="$personal_dir" ;;
  project)  target_root="${project_path%/}/${project_dir}" ;;
  *)        echo "Internal error: invalid scope '$scope'" >&2; exit 1 ;;
esac

if [[ ${#skills[@]} -eq 0 ]]; then
  skills=("${ALL_SKILLS[@]}")
fi

mkdir -p "$target_root"

for skill in "${skills[@]}"; do
  src=""
  for root in "${SKILL_ROOTS[@]}"; do
    if [[ -f "${root}/${skill}/SKILL.md" ]]; then
      src="${root}/${skill}"
      break
    fi
  done
  dest="${target_root}/${skill}"

  if [[ -z "$src" ]]; then
    echo "Skipping ${skill}: no such skill in ${SCRIPT_DIR} or ${SCRIPT_DIR}/custom-design-skills" >&2
    continue
  fi

  if [[ -e "$dest" ]]; then
    if [[ $force -eq 0 ]]; then
      read -r -p "${dest} already exists. Overwrite? [y/N] " ans
      case "$ans" in [yY]|[yY][eE][sS]) ;; *) echo "  -> skipped"; continue ;; esac
    fi
    rm -rf "$dest"
  fi

  cp -R "$src" "$dest"
  echo "Installed ${skill} -> ${dest}"
done

echo
case "$agent" in
  claude)      agent_name="Claude Code"; prefix="/" ;;
  codex)       agent_name="Codex";       prefix="\$" ;;
  antigravity) agent_name="Antigravity"; prefix="/" ;;
esac
echo "Done. Start a new ${agent_name} session in the project and try:"
for skill in "${skills[@]}"; do
  case "$skill" in
    spring-boot-vsa)        echo '  - "scaffold a new payment feature slice"   (uses spring-boot-vsa)' ;;
    spring-boot-ai)         echo '  - "how do I parse this LLM JSON into a Java record"   (uses spring-boot-ai)' ;;
    angular-vertical-slice) echo '  - "add an invoices feature using our Angular conventions"   (uses angular-vertical-slice)' ;;
    design-principles-review-by-max) echo "  - ${prefix}design-principles-review-by-max help" ;;
  esac
done
