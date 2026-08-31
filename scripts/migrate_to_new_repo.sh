#!/usr/bin/env bash
# migrate_to_new_repo.sh -- move this trip app into a brand-new GitHub repository.
#
# Run this AFTER creating an empty repo on GitHub (no README, no .gitignore, no
# licence -- it must be completely empty or the push will be rejected).
#
# Usage:
#   scripts/migrate_to_new_repo.sh <new-repo-url> [--squash] [--skip-build-check] [--remote NAME]
#
# Examples:
#   scripts/migrate_to_new_repo.sh https://github.com/GlennPiper/washington_cascades_adventure_2026.git
#   scripts/migrate_to_new_repo.sh https://github.com/GlennPiper/washington_cascades_adventure_2026.git --squash
#
# Default behaviour keeps the full commit history, which preserves the record of
# how the app was retargeted from the previous trip. Pass --squash for a single
# clean initial commit instead; the old repo remains as the archive either way.
#
# This script does not delete anything and does not touch the old remote.

set -euo pipefail

RED=$'\033[31m'; GRN=$'\033[32m'; YEL=$'\033[33m'; BLD=$'\033[1m'; RST=$'\033[0m'
die() { printf '%s\n' "${RED}error:${RST} $*" >&2; exit 1; }
note() { printf '%s\n' "${BLD}==>${RST} $*"; }

NEW_URL=""
SQUASH=0
REMOTE_NAME="newrepo"
SKIP_BUILD=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --squash) SQUASH=1; shift ;;
    --skip-build-check) SKIP_BUILD=1; shift ;;
    --remote) REMOTE_NAME="${2:?--remote needs a value}"; shift 2 ;;
    # Print the leading comment block only: skip the shebang, stop at the first
    # line that isn't a comment.
    -h|--help) awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"; exit 0 ;;
    -*) die "unknown option: $1" ;;
    *) [[ -z "$NEW_URL" ]] || die "unexpected argument: $1"; NEW_URL="$1"; shift ;;
  esac
done

[[ -n "$NEW_URL" ]] || die "missing new repo URL. See --help."

cd "$(git rev-parse --show-toplevel)"

# ---- Preconditions -------------------------------------------------------
note "Checking preconditions"

if [[ -n "$(git status --porcelain)" ]]; then
  git status --short
  die "working tree is not clean. Commit or stash first."
fi

CUR_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "    current branch: $CUR_BRANCH"
echo "    commits:        $(git rev-list --count HEAD)"
echo "    new remote:     $REMOTE_NAME -> $NEW_URL"
echo "    history mode:   $([[ $SQUASH -eq 1 ]] && echo 'squash to one initial commit' || echo 'preserve full history')"

# A build should succeed before we hand this to a new repo whose first push
# triggers a deploy. This needs the optional build deps, so it degrades to a
# warning rather than blocking a migration from a machine that lacks them.
if [[ $SKIP_BUILD -eq 1 ]]; then
  note "Skipping the build check (--skip-build-check)"
elif ! python3 -c 'import markdown, PIL' >/dev/null 2>&1; then
  note "Skipping the build check"
  printf '%s\n' "    Build deps not installed here. To run it:"
  printf '%s\n' "      pip install markdown pillow 'qrcode[pil]'"
  printf '%s\n' "    Safe to skip: CI rebuilds everything from source on push."
else
  note "Verifying the build runs clean"
  python3 scripts/parse_route_gpx.py    >/dev/null
  python3 scripts/analyze_route.py      >/dev/null
  python3 scripts/build_trip_data.py    >/dev/null
  python3 scripts/build_pwa_icons.py    >/dev/null
  python3 scripts/build_deliverables.py >/dev/null
  SITE_URL="" python3 scripts/build_pwa_assets.py >/dev/null
  echo "    build OK"

  # The build regenerates tracked HTML; if that produced a diff, the committed
  # deliverables were stale. Surface it rather than pushing a mismatch.
  if [[ -n "$(git status --porcelain)" ]]; then
    git status --short
    printf '%s\n' "${YEL}warning:${RST} the build changed tracked files, meaning the committed"
    printf '%s\n' "         deliverables were stale. Commit these before migrating."
    exit 1
  fi
fi

# ---- Push ----------------------------------------------------------------
if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  note "Remote '$REMOTE_NAME' already exists; updating its URL"
  git remote set-url "$REMOTE_NAME" "$NEW_URL"
else
  note "Adding remote '$REMOTE_NAME'"
  git remote add "$REMOTE_NAME" "$NEW_URL"
fi

if [[ $SQUASH -eq 1 ]]; then
  note "Building a single-commit history on a temporary branch"
  TMP_BRANCH="migrate-squash-$$"
  git checkout -q --orphan "$TMP_BRANCH"
  git add -A
  git commit -q -m "Washington Cascades Adventure Route trip app

Offline-first PWA and planning workspace for the September 8-13, 2026 route
through Gifford Pinchot National Forest.

Retargeted from an earlier San Rafael Swell trip app; see README.md for the
pipeline and the retargeting guide. Full development history lives in the
predecessor repository."
  note "Pushing to $REMOTE_NAME as main"
  git push -u "$REMOTE_NAME" "$TMP_BRANCH":main
  git checkout -q "$CUR_BRANCH"
  git branch -D "$TMP_BRANCH" >/dev/null
else
  note "Pushing $CUR_BRANCH to $REMOTE_NAME as main (full history)"
  git push -u "$REMOTE_NAME" "$CUR_BRANCH":main
fi

# ---- Next steps ----------------------------------------------------------
# Only derive github.com URLs when the remote actually is one; a local path or
# another host would otherwise produce nonsense like https://github.com//tmp/x.
if [[ "$NEW_URL" =~ ^(git@github\.com:|https://github\.com/)([^/]+)/(.+?)(\.git)?$ ]]; then
  OWNER="${BASH_REMATCH[2]}"
  REPO="${BASH_REMATCH[3]%.git}"
  OWNER_REPO="$OWNER/$REPO"
else
  printf '\n%s\n' "${GRN}Pushed.${RST} Remote is not a github.com URL, so the"
  printf '%s\n' "  usual next steps (enable Pages with Source: GitHub Actions, re-run the"
  printf '%s\n' "  deploy, then check https://<owner>.github.io/<repo>/) do not apply verbatim."
  printf '%s\n\n' "  The old remote is untouched."
  exit 0
fi

cat <<EOF

${GRN}Pushed.${RST} ${BLD}Three things left, all in the GitHub web UI:${RST}

  ${BLD}1. Enable Pages${RST}
     https://github.com/$OWNER_REPO/settings/pages
     Set ${BLD}Source: GitHub Actions${RST} (not "Deploy from a branch").

  ${BLD}2. Re-run the deploy${RST}
     https://github.com/$OWNER_REPO/actions
     The first push may have failed at the deploy step because Pages was not
     enabled yet. Re-run the latest workflow after step 1.

  ${BLD}3. Confirm the site${RST}
     https://$OWNER.github.io/$REPO/
     The QR code on the landing page is generated from that URL at build time,
     so it updates itself. Check that the install page loads and the itinerary
     map renders.

${BLD}If you want an agent to keep working in the new repo:${RST}
  Authorize the Cursor GitHub App on $OWNER_REPO, then start a fresh agent
  there. An agent's token is scoped to a single repository, so this workspace
  cannot see or push to the new repo.

${BLD}The old repo is untouched.${RST} Keep it as the archive, or archive it in
  settings once the new site is confirmed working.
EOF
