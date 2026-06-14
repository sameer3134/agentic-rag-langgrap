#!/usr/bin/env bash
# make-worktrees.sh — create a git worktree for a single PR branch
# Usage: bash .claude/scripts/make-worktrees.sh --pr-id PR-N --branch feat/foo --slug foo [--force]
set -euo pipefail

# ── Argument parsing ────────────────────────────────────────────────────────
PR_ID=""
BRANCH=""
SLUG=""
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr-id)   PR_ID="$2";   shift 2 ;;
    --branch)  BRANCH="$2";  shift 2 ;;
    --slug)    SLUG="$2";    shift 2 ;;
    --force)   FORCE=1;      shift   ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$PR_ID" || -z "$BRANCH" || -z "$SLUG" ]]; then
  echo "Error: --pr-id, --branch, and --slug are all required." >&2
  exit 1
fi

# ── Resolve repo root (script lives in .claude/scripts/) ───────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ── Read config files ───────────────────────────────────────────────────────
PREFIX_FILE="$REPO_ROOT/.claude/worktree-prefix"
SYMLINKS_FILE="$REPO_ROOT/.claude/worktree-symlinks"

if [[ ! -f "$PREFIX_FILE" ]]; then
  echo "Error: .claude/worktree-prefix not found at $PREFIX_FILE" >&2
  exit 1
fi

PREFIX="$(cat "$PREFIX_FILE" | tr -d '[:space:]')"
WORKTREE_PATH="$REPO_ROOT/${PREFIX}${SLUG}"

echo "[$PR_ID] Branch:    $BRANCH"
echo "[$PR_ID] Worktree:  $WORKTREE_PATH"

# ── Create the branch if it doesn't exist ──────────────────────────────────
cd "$REPO_ROOT"
if ! git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "[$PR_ID] Creating branch: $BRANCH"
  git branch "$BRANCH" HEAD
else
  echo "[$PR_ID] Branch already exists: $BRANCH"
fi

# ── Create (or re-use) the worktree ────────────────────────────────────────
if [[ -d "$WORKTREE_PATH" ]]; then
  if [[ "$FORCE" -eq 1 ]]; then
    echo "[$PR_ID] Worktree already exists — skipping (--force is a no-op here, worktree intact)"
  else
    echo "[$PR_ID] Worktree already exists at $WORKTREE_PATH — skipping" >&2
    exit 0
  fi
else
  git worktree add "$WORKTREE_PATH" "$BRANCH"
  echo "[$PR_ID] Worktree created."
fi

# ── Symlink shared resources ────────────────────────────────────────────────
if [[ -f "$SYMLINKS_FILE" ]]; then
  echo "[$PR_ID] Setting up symlinks..."
  while IFS= read -r item || [[ -n "$item" ]]; do
    # Skip blank lines and comments
    [[ -z "$item" || "$item" == \#* ]] && continue

    SRC="$REPO_ROOT/$item"
    DEST="$WORKTREE_PATH/$item"

    if [[ ! -e "$SRC" && ! -L "$SRC" ]]; then
      echo "[$PR_ID]   SKIP $item (source does not exist yet)"
      continue
    fi

    # Create parent directory in worktree if needed
    DEST_PARENT="$(dirname "$DEST")"
    mkdir -p "$DEST_PARENT"

    if [[ -L "$DEST" ]]; then
      echo "[$PR_ID]   EXISTS $item (symlink already present)"
    elif [[ -e "$DEST" ]]; then
      echo "[$PR_ID]   SKIP $item (real file exists in worktree — not overwriting)"
    else
      ln -s "$SRC" "$DEST"
      echo "[$PR_ID]   LINKED $item -> $SRC"
    fi
  done < "$SYMLINKS_FILE"
fi

echo "[$PR_ID] Done. Worktree ready at: $WORKTREE_PATH"
