#!/usr/bin/env bash
# sync-pypi-version.sh — reconcile local pyproject.toml and git tags with
# whatever version CI just published to PyPI.
#
# WHY THIS EXISTS:
#   The wads CI auto-bumps the patch version, publishes to PyPI (works),
#   then tries to push the bump commit + tag back via SSH (fails — no
#   SSH_PRIVATE_KEY secret set on the repo). Result: PyPI is ahead of the
#   local repo. Until setup-ssh-deploy-key.sh is run, this script is the
#   manual reconciliation step.
#
# WHAT IT DOES:
#   1. Curl PyPI for the current published version of typola.
#   2. Read pyproject.toml's local version.
#   3. If they differ: edit pyproject.toml, commit with [skip ci], tag,
#      push main and tag.
#   4. If they match: report no-op.
#
# USAGE:
#   bash sync-pypi-version.sh             # interactive (prompts before push)
#   bash sync-pypi-version.sh --yes       # skip the confirm prompt

set -euo pipefail

# This script lives at <repo>/skills/typola-dev/scripts/, so the repo root is
# three levels up. Override with TYPOLA_REPO_DIR when running it from elsewhere.
# `-P` so an invocation through the ~/.claude/skills symlink still resolves to
# the real checkout rather than to ~/.claude.
SKILL_SCRIPTS_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_DIR="${TYPOLA_REPO_DIR:-$(cd -P "$SKILL_SCRIPTS_DIR/../../.." && pwd -P)}"
AUTO_YES=0
[[ "${1:-}" == "--yes" ]] && AUTO_YES=1

cd "$REPO_DIR"

# Fetch current PyPI version (cache-bust with a random query param).
PYPI_VERSION=$(curl -s "https://pypi.org/pypi/typola/json?_=$RANDOM" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["info"]["version"])')

if [[ -z "$PYPI_VERSION" ]]; then
  echo "ERROR: could not read PyPI version. Is the package published?"
  exit 1
fi

# Read local version from pyproject.toml.
LOCAL_VERSION=$(python3 -c '
import re, pathlib
text = pathlib.Path("pyproject.toml").read_text()
m = re.search(r"^version\s*=\s*\"([^\"]+)\"", text, re.M)
print(m.group(1) if m else "")
')

if [[ -z "$LOCAL_VERSION" ]]; then
  echo "ERROR: could not parse version from pyproject.toml"
  exit 1
fi

echo "PyPI version:  $PYPI_VERSION"
echo "Local version: $LOCAL_VERSION"

if [[ "$PYPI_VERSION" == "$LOCAL_VERSION" ]]; then
  echo "Already in sync. Nothing to do."
  # Even if pyproject.toml matches, the tag may not exist remotely. Report.
  if ! git rev-parse --verify "v$PYPI_VERSION" >/dev/null 2>&1; then
    echo "Note: tag v$PYPI_VERSION does not exist locally. You may want to create + push it:"
    echo "  git tag -a v$PYPI_VERSION -m 'Release version $PYPI_VERSION'"
    echo "  git push origin v$PYPI_VERSION"
  fi
  exit 0
fi

# Refuse to "downgrade" if local is ahead — that means something weird happened.
python3 - <<PY
from packaging.version import Version
import sys
local = Version("$LOCAL_VERSION")
pypi  = Version("$PYPI_VERSION")
if local > pypi:
    print(f"REFUSING: local version ({local}) is AHEAD of PyPI ({pypi}).")
    print("This is unusual — investigate before syncing. Nothing changed.")
    sys.exit(2)
PY

# Confirm.
echo
echo "Plan:"
echo "  1. Edit pyproject.toml: version $LOCAL_VERSION → $PYPI_VERSION"
echo "  2. git commit -m 'Sync version to $PYPI_VERSION [skip ci]'"
echo "  3. git tag -a v$PYPI_VERSION -m 'Release version $PYPI_VERSION'"
echo "  4. git push origin main"
echo "  5. git push origin v$PYPI_VERSION"
echo
if [[ "$AUTO_YES" -ne 1 ]]; then
  read -r -p "Proceed? [y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
fi

# Apply the version change in-place. Targets the project version line specifically;
# other "version =" lines (build-system requires, etc.) are quoted with operators.
python3 - <<PY
import pathlib, re
p = pathlib.Path("pyproject.toml")
text = p.read_text()
new_text = re.sub(
    r'^(version\s*=\s*)"[^"]+"',
    f'\\1"$PYPI_VERSION"',
    text,
    count=1,
    flags=re.M,
)
if new_text == text:
    raise SystemExit("ERROR: no version line modified — check pyproject.toml format.")
p.write_text(new_text)
PY

git add pyproject.toml
git commit -m "Sync version to $PYPI_VERSION [skip ci]"
git tag -a "v$PYPI_VERSION" -m "Release version $PYPI_VERSION"
git push origin main
git push origin "v$PYPI_VERSION"

echo
echo "Done. PyPI and local are in sync at $PYPI_VERSION."
echo "Tag v$PYPI_VERSION pushed."
