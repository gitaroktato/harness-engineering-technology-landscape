#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT_DIR="$ROOT/.agents/sessions"

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
fi

command -v opencode >/dev/null || {
  echo "error: opencode not found in PATH" >&2
  exit 1
}
command -v jq >/dev/null || {
  echo "error: jq not found in PATH" >&2
  exit 1
}

mkdir -p "$OUT_DIR"

new=0
updated=0
skipped=0

listing="$(opencode session list --format json | jq -r --arg dir "$ROOT" '.[] | select(.directory == $dir and .updated != null) | [.id, (.updated|tostring)] | @tsv')" || {
  echo "error: failed to list sessions for $ROOT" >&2
  exit 1
}

while IFS=$'\t' read -r id updated_ms; do
  [[ -n "$id" ]] || continue
  target="$OUT_DIR/$id.json"
  if [[ $FORCE -eq 0 && -f "$target" ]]; then
    file_ms=$(($(stat -c %Y "$target") * 1000))
    valid=0
    jq empty "$target" >/dev/null 2>&1 && valid=1
    if ((file_ms >= updated_ms)) && ((valid)); then
      echo "skip   $id (up to date)"
      skipped=$((skipped + 1))
      continue
    fi
    if ((! valid)); then
      echo "update $id (corrupt export, re-exporting)"
    else
      echo "update $id (session changed since export)"
    fi
    updated=$((updated + 1))
  else
    if [[ -f "$target" ]]; then
      echo "force  $id"
      updated=$((updated + 1))
    else
      echo "new    $id"
      new=$((new + 1))
    fi
  fi
  opencode export "$id" >"$target"
done <<<"$listing"

echo "done: $new new, $updated updated, $skipped skipped -> $OUT_DIR"
