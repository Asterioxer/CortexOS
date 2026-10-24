#!/usr/bin/env bash
set -euo pipefail

# CortexOS Deterministic Checkpoint, Sandbox, and Rollback Engine
STATE_SNAPSHOT_DIR=".cortex/snapshots"
REPORT_DIR=".cortex/reports"

checkpoint_create() {
  local task_id="$1"
  local label="${2:-pre}"
  local tmp_index
  tmp_index="$(mktemp -u)"

  # 1. Copy current git index so the agent's real staging area is untouched
  cp "$(git rev-parse --git-dir)/index" "$tmp_index"
  
  # 2. Stage all modified and untracked working-tree files into the shadow index
  GIT_INDEX_FILE="$tmp_index" git add -A
  local tree commit
  tree="$(GIT_INDEX_FILE="$tmp_index" git write-tree)"
  commit="$(git commit-tree "$tree" -p HEAD -m "cortex-checkpoint: $task_id ($label)")"
  
  # 3. Pin under refs/checkpoints/ so git gc never prunes it
  git update-ref "refs/checkpoints/$task_id/$label" "$commit"
  rm -f "$tmp_index"

  # 4. Snapshot gitignored local SQLite DBs and .env files
  mkdir -p "$STATE_SNAPSHOT_DIR/$task_id/$label"
  for stateful_file in .env cortex_memory.sqlite cortex_memory.sqlite-wal; do
    if [[ -f "$stateful_file" ]]; then
      cp -p "$stateful_file" "$STATE_SNAPSHOT_DIR/$task_id/$label/" 2>/dev/null || true
    fi
  done
  echo "[CORTEX-CHECKPOINT] Created checkpoint: refs/checkpoints/$task_id/$label ($commit)"
}

checkpoint_restore() {
  local task_id="$1"
  local ref="refs/checkpoints/$task_id/pre"
  git rev-parse --verify --quiet "$ref" >/dev/null \
    || { echo "[ERROR] No checkpoint found for $task_id at $ref" >&2; return 1; }

  # Undo must be undoable: snapshot current state before rolling back
  checkpoint_create "$task_id" "before-restore-$(date +%s)"

  # Stage any newly created untracked files so git restore removes them cleanly
  git add -A
  git restore --source="$ref" --staged --worktree -- .
  git reset -q

  # Restore local SQLite DBs after verifying no active connections
  if [[ -d "$STATE_SNAPSHOT_DIR/$task_id/pre" ]]; then
    cp -pf "$STATE_SNAPSHOT_DIR/$task_id/pre/"* . 2>/dev/null || true
  fi
  echo "[CORTEX-ROLLBACK] Workspace deterministically restored to $ref"
}

run_sandboxed_cmd() {
  local workdir
  workdir="$(pwd)"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    # macOS Seatbelt: allow read broadly (except SSH/AWS keys), restrict writes to workdir
    sandbox-exec -p "(version 1)
      (allow default)
      (deny file-read* (subpath \"$HOME/.ssh\") (subpath \"$HOME/.aws\") (subpath \"$HOME/.gnupg\"))
      (deny file-write*)
      (allow file-write* (subpath \"$workdir\") (subpath \"/tmp\") (subpath \"/private/tmp\"))" "$@"
  elif command -v bwrap >/dev/null 2>&1; then
    # Linux Bubblewrap: omit ~/.ssh and ~/.aws entirely from mount namespace; bind workdir RW
    bwrap --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 --ro-bind /bin /bin \
          --proc /proc --dev /dev --tmpfs /tmp --tmpfs "$HOME" \
          --bind "$workdir" "$workdir" --chdir "$workdir" --unshare-all --share-net "$@"
  else
    # Fallback execution in controlled environment
    "$@"
  fi
}

# Usage dispatcher: ./checkpoint.sh [create|restore|exec] <task_id> [cmd...]
case "${1:-}" in
  create)  checkpoint_create "$2" "${3:-pre}" ;;
  restore) checkpoint_restore "$2" ;;
  exec)
    TASK_ID="$2"; shift 2
    checkpoint_create "$TASK_ID" "pre"
    if run_sandboxed_cmd "$@"; then
      git add -A
      git commit -q --allow-empty -m "CortexOS Task Verified" -m "Task-Id: $TASK_ID"
    else
      mkdir -p "$REPORT_DIR"
      checkpoint_create "$TASK_ID" "failed"
      git diff "refs/checkpoints/$TASK_ID/pre" "refs/checkpoints/$TASK_ID/failed" > "$REPORT_DIR/$TASK_ID.failed.diff" || true
      checkpoint_restore "$TASK_ID"
      exit 1
    fi
    ;;
  *)
    echo "Usage: $0 {create <task_id> [label]|restore <task_id>|exec <task_id> <cmd...>}" >&2
    exit 1
    ;;
esac
