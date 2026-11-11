#!/usr/bin/env bash
#
# Install the Claude Code skills in this repository.
# Default: spring-boot-ai and spring-boot-vsa. Other skills are installed by name.
#
#   ./install.sh --personal                    # ~/.claude/skills/<skill>/
#   ./install.sh --project /path/to/proj       # <proj>/.claude/skills/<skill>/
#   ./install.sh --skill spring-boot-vsa --personal
#   ./install.sh --skill design-principles-review-by-max --project /path/to/proj
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

usage() {
  cat <<EOF
Install the Claude Code skills in this repository.

Usage:
  $0 --personal [--skill NAME] [--force]
  $0 --project PATH [--skill NAME] [--force]
  $0                    # interactive

Options:
  --personal            Install to \$HOME/.claude/skills/
  --project PATH        Install to PATH/.claude/skills/
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

case "$scope" in
  personal) target_root="${HOME}/.claude/skills" ;;
  project)  target_root="${project_path%/}/.claude/skills" ;;
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
echo "Done. Open Claude Code in the project and try:"
echo '  - "scaffold a new payment feature slice"   (triggers spring-boot-vsa)'
echo '  - "how do I parse this LLM JSON into a Java record"   (triggers spring-boot-ai)'
echo '  - "run a design principles review of this screen"   (triggers design-principles-review-by-max)'
