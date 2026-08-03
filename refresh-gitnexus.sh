#!/usr/bin/env bash
#
# refresh-gitnexus.sh — keep the ThreeSides GitNexus indexes fresh.
#
# What it does, EVERY run, no flags needed:
#   1. per repo: stash uncommitted changes → git pull --ff-only
#      → (index) → re-apply the stash. This way a WIP tree doesn't block the pull;
#      the fresh code gets indexed, then your local changes come back on top.
#   2. gitnexus analyze each repo (INCREMENTAL — re-parses only changed files,
#      no-op if the index is already up to date, so it's cheap to run often).
#      If it fails with a corrupt-FTS-index error, auto `gitnexus clean --force`
#      + full re-analyze, once, before giving up.
#   3. gitnexus group sync <group>  → rebuilds the cross-repo contract registry
#
# Usage:
#   ./refresh-gitnexus.sh                                    # pull + index all repos + resync group
#   ./refresh-gitnexus.sh --no-pull                          # skip the git pull, index-only
#   ./refresh-gitnexus.sh threease_backend threease_ticket   # only these repos (still pulls)
#   ./refresh-gitnexus.sh --no-pull threease_pro             # combine
#
set -uo pipefail

# Tự nhận diện thư mục chứa script (workspace root), KHÔNG hard-code path máy ai —
# để ai clone/pull script này ở máy nào, path nào cũng chạy đúng.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GROUP="threease"
ALL_REPOS=(threease_backend threease_admin threease_pro threease_reservation threease_ticket)

DO_PULL=1
SELECTED=()
for arg in "$@"; do
  case "$arg" in
    --pull) DO_PULL=1 ;;
    --no-pull) DO_PULL=0 ;;
    -h|--help) sed -n '2,21p' "$0"; exit 0 ;;
    *) SELECTED+=("$arg") ;;
  esac
done
# If no repos named, do all of them.
REPOS=("${SELECTED[@]:-${ALL_REPOS[@]}}")

command -v gitnexus >/dev/null || { echo "❌ gitnexus not on PATH (npm i -g gitnexus)"; exit 1; }

echo "🔄 Refreshing GitNexus for: ${REPOS[*]}"
[ "$DO_PULL" -eq 1 ] && echo "   (pulling latest first — pass --no-pull to skip)"
echo

for r in "${REPOS[@]}"; do
  dir="$ROOT/$r"
  if [ ! -d "$dir/.git" ]; then
    echo "⏭️  $r — skipped (not a git repo at $dir)"
    continue
  fi
  echo "── $r ──────────────────────────────────"
  stashed=0
  if [ "$DO_PULL" -eq 1 ]; then
    # Nếu có thay đổi chưa commit (tracked) → stash lại để `pull --ff-only` không bị chặn.
    # (untracked files không tính — chúng hiếm khi chặn ff-only.)
    if [ -n "$(git -C "$dir" status --porcelain --untracked-files=no)" ]; then
      if git -C "$dir" stash push -m "refresh-gitnexus auto-stash" >/dev/null 2>&1; then
        stashed=1
        echo "   📦 stashed local changes (sẽ apply lại sau khi index)"
      else
        echo "   ⚠️  stash thất bại — pull có thể bị chặn"
      fi
    fi
    git -C "$dir" pull --ff-only \
      || echo "   ⚠️  pull --ff-only thất bại (diverged / untracked conflict) — index cây hiện tại"
  fi

  # Index CODE MỚI vừa pull (trước khi apply lại stash).
  if ! ( cd "$dir" && gitnexus analyze ); then
    echo "   ⚠️  analyze failed for $r — thử tự phục hồi (clean --force + re-analyze full)"
    if ( cd "$dir" && gitnexus clean --force ) >/dev/null 2>&1 && ( cd "$dir" && gitnexus analyze ); then
      echo "   ✅ đã tự phục hồi index cho $r"
    else
      echo "   ❌ vẫn lỗi sau khi tự phục hồi — $r cần xem tay"
    fi
  fi

  # Apply lại phần sửa dở SAU khi đã index xong.
  if [ "$stashed" -eq 1 ]; then
    if git -C "$dir" stash pop >/dev/null 2>&1; then
      echo "   📤 đã apply lại local changes"
    else
      echo "   ⚠️  stash pop CONFLICT — thay đổi của bạn vẫn an toàn trong 'git stash list' (repo: $r), giải quyết tay"
    fi
  fi
  echo
done

echo "── group sync: $GROUP ──────────────────────"
gitnexus group sync "$GROUP" || echo "   ⚠️  group sync failed"

echo
echo "✅ Done. Check freshness anytime with:  gitnexus group status $GROUP"
