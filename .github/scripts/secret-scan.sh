#!/usr/bin/env bash
# secret-scan.sh -- final PII guard for the deploy workflow.
#
# Greps the staged publish directory for:
#   1. Participant first names (hardcoded list).
#   2. Email addresses.
#   3. Phone numbers in common US formats.
#
# An allow-list of public emergency / agency contacts is stripped from the
# output before deciding whether the scan failed. Any line that survives
# both filters is treated as a leak and fails the deploy.
#
# Usage: secret-scan.sh <staged_dir>

set -euo pipefail

STAGE="${1:-_publish}"

if [[ ! -d "$STAGE" ]]; then
  echo "secret-scan: staging dir '$STAGE' not found" >&2
  exit 2
fi

# Hardcoded participant first/last names. Keep this list in sync with the
# local-only Participants.md roster. Adding names here only matters for the
# scan -- they never appear in any tracked file.
NAMES=(
  "Glenn"
  "Vahnessa"
  "Helligso"
  "Stradley"
  "O'Kelley"
  "Strandley"
  "Chanbers"
  "Chuck"
  "Robbie"
  "Tresa"
  "Bermeo"
  "Hooste"
  "Hoosete"
  "Jamie"
  "Jacob"
  "Andi"
  "Adrian"
)

# Public agency / emergency contacts (allowed to appear in published HTML).
# We accept each number in three forms: the tel: URL form (with or without
# +1), the (NNN) NNN-NNNN display form, and the bare NNN-NNN-NNNN form.
ALLOW_NUMBERS=(
  "4353812404"   # Emery County Sheriff / SAR
  "4352598115"   # Grand County Sheriff
  "8018873800"   # Utah Highway Patrol
  "4356363600"   # BLM Price
  "4352592100"   # BLM Moab
  "4352592444"   # Sand Flats Recreation Area (Grand County / fee program)
  "4352597155"   # Manti-La Sal NF / La Sal Ranger District (public line on trip pages)
)

ALLOW_PHONE_RE=""
for n in "${ALLOW_NUMBERS[@]}"; do
  a="${n:0:3}"; b="${n:3:3}"; c="${n:6:4}"
  ALLOW_PHONE_RE+="tel:\\+?1?${n}|\\(${a}\\) ?${b}-${c}|${a}[-. ]${b}[-. ]${c}|"
done
ALLOW_PHONE_RE="(${ALLOW_PHONE_RE%|})"

# Build the names regex (word-boundary on both sides, case-sensitive on
# purpose -- matching first names is signal, lowercase common words aren't).
NAME_RE=""
for n in "${NAMES[@]}"; do
  NAME_RE+="${n}|"
done
NAME_RE="\\b(${NAME_RE%|})\\b"

# Phone regex -- deliberately strict so it doesn't false-match against GPX
# coordinates or JSON lat/lon values (which contain long runs of digits).
# A real phone number must be ONE of:
#   1. tel: URL (with optional +1 prefix), e.g. tel:+14353812404
#   2. (NNN) NNN-NNNN display form, e.g. (435) 381-2404
#   3. NNN-NNN-NNNN or NNN.NNN.NNNN -- requires actual separators in BOTH
#      positions. (NNN.NNNNNNNNN style coordinate strings have only one dot
#      so they can't match.)
PHONE_RE='tel:\+?1?[0-9]{10}|\([0-9]{3}\) ?[0-9]{3}[-. ][0-9]{4}|\b[0-9]{3}[-.][0-9]{3}[-.][0-9]{4}\b'

# Email regex.
EMAIL_RE='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'

# Some files in the publish dir are huge inlined assets (base64 images).
# Restrict the scan to text-y file extensions to keep it fast and to avoid
# false positives in binary blobs.
TEXT_GLOBS=(
  "*.html" "*.htm"
  "*.js" "*.css"
  "*.json" "*.webmanifest"
  "*.gpx" "*.xml"
  "*.svg"
  "*.txt" "*.md"
)
INCLUDE_ARGS=()
for g in "${TEXT_GLOBS[@]}"; do
  INCLUDE_ARGS+=(--include="$g")
done

scan() {
  local label="$1"
  local pattern="$2"
  # grep -E (extended), -r (recursive), -n (line number), -H (filename),
  # -I (skip binaries). May exit 1 if no match -- that's the success case.
  local matches
  if matches=$(grep -E -r -n -H -I "${INCLUDE_ARGS[@]}" "$pattern" "$STAGE" 2>/dev/null); then
    # Strip allow-listed phone numbers from the matches.
    local filtered
    filtered=$(printf '%s\n' "$matches" | grep -E -v "$ALLOW_PHONE_RE" || true)
    if [[ -n "$filtered" ]]; then
      echo "secret-scan: $label hits in $STAGE/" >&2
      printf '%s\n' "$filtered" | head -50 >&2
      return 1
    fi
  fi
  return 0
}

failed=0
scan "participant name"     "$NAME_RE"  || failed=1
scan "phone number"         "$PHONE_RE" || failed=1
scan "email address"        "$EMAIL_RE" || failed=1

if [[ $failed -ne 0 ]]; then
  echo "secret-scan: FAILED -- review the hits above and remove the leak before re-deploying." >&2
  exit 1
fi

echo "secret-scan: OK (no PII leaks in $STAGE/)"
