#!/usr/bin/env bash
# setup-ssh-deploy-key.sh — guided one-time setup of an SSH deploy key
# for the typola GitHub repo, so the wads CI can push the auto-bumped
# version + tag back to main.
#
# WHY THIS EXISTS:
#   The wads CI workflow's "Commit Changes" + "Tag Repository" steps
#   push back via SSH using `secrets.SSH_PRIVATE_KEY`. Without that
#   secret set, the steps fail and you have to run sync-pypi-version.sh
#   manually after every merge to main. Once this script is run once,
#   that whole dance disappears.
#
# WHAT IT DOES:
#   1. Generates a fresh ed25519 keypair at ~/.ssh/typola_deploy[.pub].
#   2. Adds the PUBLIC key to the typola repo's deploy keys (with
#      write access). You'll be prompted to confirm.
#   3. Sets the PRIVATE key as the SSH_PRIVATE_KEY secret on the repo
#      via gh secret set.
#   4. Adds a known_hosts entry so the runner trusts github.com.
#
# REQUIREMENTS:
#   - gh CLI authenticated with admin access on the repo.
#   - ssh-keygen + curl available.
#
# USAGE:
#   bash setup-ssh-deploy-key.sh

set -euo pipefail

REPO="thorwhalen/typola"
KEY_PATH="$HOME/.ssh/typola_deploy"
KEY_TITLE="typola-ci-bumpback"

echo "=== One-time SSH deploy key setup for $REPO ==="
echo
echo "This will:"
echo "  1. Generate a new ed25519 keypair at $KEY_PATH (and $KEY_PATH.pub)"
echo "  2. Add the public key as a deploy key on $REPO with write access"
echo "  3. Store the private key as the SSH_PRIVATE_KEY secret on $REPO"
echo
echo "After this, the wads CI's auto-bump-and-push-back will work, and"
echo "sync-pypi-version.sh becomes unnecessary."
echo

read -r -p "Proceed? [y/N] " ans
[[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }

# 1. Generate keypair (no passphrase — CI can't enter one).
if [[ -f "$KEY_PATH" || -f "$KEY_PATH.pub" ]]; then
  echo "WARNING: $KEY_PATH already exists. Pick another path or back up + remove it first."
  exit 1
fi

ssh-keygen -t ed25519 -N "" -C "typola-ci-bumpback@github" -f "$KEY_PATH"
chmod 600 "$KEY_PATH"

# 2. Add deploy key (with write access) via the GitHub API.
echo
echo "Adding deploy key to $REPO (write access)..."
PUB_KEY="$(cat "$KEY_PATH.pub")"

gh api -X POST "repos/$REPO/keys" \
  -f title="$KEY_TITLE" \
  -f key="$PUB_KEY" \
  -F read_only=false \
  >/dev/null

echo "Deploy key added."

# 3. Set the SSH_PRIVATE_KEY secret on the repo.
echo
echo "Setting SSH_PRIVATE_KEY secret on $REPO..."
gh secret set SSH_PRIVATE_KEY --body "$(cat "$KEY_PATH")" -R "$REPO"
echo "Secret set."

echo
echo "=== Done ==="
echo
echo "Verify by merging any small change to main and watching the CI run."
echo "The 'Commit Changes' and 'Tag Repository' steps should now succeed."
echo
echo "If you ever want to revoke this key:"
echo "  gh api -X DELETE repos/$REPO/keys/<key-id>"
echo "  gh secret delete SSH_PRIVATE_KEY -R $REPO"
echo "  rm $KEY_PATH $KEY_PATH.pub"
