#!/usr/bin/env bash
# Clones (or updates) the lior-claude-skills repo and symlinks every skill
# folder into ~/.claude/skills so Claude Code picks them up automatically.
# Safe to re-run any time — on login, after a reboot, on a freshly imaged
# lab PC, whenever. It only ever touches symlinks it created.

set -eo pipefail

# ---- Edit these two lines for your setup ----
REPO_URL="https://github.com/liorkishipro-ai/lior-claude-skills.git"
CLONE_DIR="$HOME/lior-claude-skills"
# ----------------------------------------------

SKILLS_DIR="$HOME/.claude/skills"

log() { printf '[install-skills] %s\n' "$1"; }
err() { printf '[install-skills] ERROR: %s\n' "$1" >&2; }

command -v git >/dev/null 2>&1 || { err "git is not installed. Install it first."; exit 1; }

# Clone on first run, pull on every run after that
if [ -d "$CLONE_DIR/.git" ]; then
  log "Updating existing clone at $CLONE_DIR"
  if ! git -C "$CLONE_DIR" pull --ff-only; then
    err "git pull failed — likely local changes or a diverged branch in $CLONE_DIR. Resolve manually, then re-run this script."
    exit 1
  fi
else
  log "Cloning $REPO_URL into $CLONE_DIR"
  git clone "$REPO_URL" "$CLONE_DIR"
fi

mkdir -p "$SKILLS_DIR"

# ---- Third-party skill packages, installed via the `skills` CLI ----
# https://github.com/vercel-labs/skills — one entry per line.
# "owner/repo" installs every skill in that repo.
# "owner/repo::skill-name" installs just one skill from a multi-skill repo.
THIRD_PARTY_SKILLS=(
  # "julianoczkowski/designer-skills"   # re-enable once base setup is verified
)
# ----------------------------------------------------------------------

if ! command -v npx >/dev/null 2>&1; then
  err "npx not found — skipping third-party skills. Install Node.js to enable this."
else
  for entry in "${THIRD_PARTY_SKILLS[@]}"; do
    repo="${entry%%::*}"
    if [[ "$entry" == *"::"* ]]; then
      skill_name="${entry##*::}"
      log "Installing '$skill_name' from $repo (npx skills)"
      if ! npx -y skills add "$repo" --skill "$skill_name" -a claude-code -g -y; then
        err "Failed to install $skill_name from $repo — continuing"
      fi
    else
      log "Installing all skills from $repo (npx skills)"
      if ! npx -y skills add "$repo" --all -a claude-code -g -y; then
        err "Failed to install skills from $repo — continuing"
      fi
    fi
  done
fi

expected=""

# Link every valid skill folder found in the repo
for skill_path in "$CLONE_DIR"/*/; do
  [ -d "$skill_path" ] || continue
  skill_name="$(basename "$skill_path")"

  case "$skill_name" in
    .*|dist|node_modules) continue ;;
  esac

  if [ ! -f "${skill_path}SKILL.md" ]; then
    log "Skipping $skill_name (no SKILL.md found)"
    continue
  fi

  expected="$expected $skill_name"
  target="$SKILLS_DIR/$skill_name"
  source_abs="$(cd "$skill_path" && pwd)"

  if [ -L "$target" ]; then
    current="$(readlink "$target")"
    if [ "$current" = "$source_abs" ]; then
      log "OK: $skill_name already linked"
    else
      log "Relinking $skill_name (was pointing elsewhere)"
      rm "$target"
      ln -s "$source_abs" "$target"
    fi
  elif [ -e "$target" ]; then
    err "$target exists and is NOT a symlink — leaving it alone (likely a name collision with a third-party skill, or something installed manually). Rename one of them if you want $skill_name managed by this script."
  else
    log "Linking $skill_name"
    ln -s "$source_abs" "$target"
  fi
done

# Prune links this script created for skills that were since removed/renamed
for existing in "$SKILLS_DIR"/*/; do
  link="${existing%/}"
  [ -L "$link" ] || continue
  name="$(basename "$link")"
  link_target="$(readlink "$link")"
  case "$link_target" in
    "$CLONE_DIR"/*)
      case " $expected " in
        *" $name "*) ;;
        *) log "Removing stale link: $name (no longer in repo)"; rm "$link" ;;
      esac
      ;;
  esac
done

log "Done. Active skills in $SKILLS_DIR:"
ls -1 "$SKILLS_DIR"