#!/usr/bin/env python3
"""rebuild-hf-space.py — trigger a fresh build of the typola HF Space.

WHY THIS EXISTS:
    When a new typola version is published to PyPI and you want the live
    Space to pick it up, the Space needs to rebuild its Docker image.
    Docker layer caching can hold onto the old `pip install` layer, so
    a "soft" restart isn't enough — we need a factory reboot.

WHAT IT DOES:
    Calls HfApi.restart_space(repo_id, factory_reboot=True), which busts
    the build cache and rebuilds from scratch. Polls the build status
    until it lands in RUNNING (success) or BUILD_ERROR/RUNTIME_ERROR.

ASSUMPTIONS:
    HF_WRITE_TOKEN env var is set. If not, sources ~/.keys.

USAGE:
    python rebuild-hf-space.py                          # default repo
    python rebuild-hf-space.py --repo OWNER/SPACE       # different Space
    python rebuild-hf-space.py --no-wait                # fire and exit
"""

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import time

DEFAULT_REPO = "thorwhalen/typola"
KEYS_FILE = pathlib.Path.home() / ".keys"


def ensure_token() -> str:
    """Return HF_WRITE_TOKEN, sourcing ~/.keys if needed."""
    tok = os.environ.get("HF_WRITE_TOKEN")
    if tok:
        return tok
    if not KEYS_FILE.is_file():
        sys.exit(f"HF_WRITE_TOKEN not set and {KEYS_FILE} does not exist.")
    # Re-exec a shell that sources ~/.keys, then prints the token. We can't
    # source into our own process, but we can read it once.
    out = subprocess.run(
        ["bash", "-c", f"source {KEYS_FILE} && printf '%s' \"$HF_WRITE_TOKEN\""],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if not out:
        sys.exit("~/.keys does not export HF_WRITE_TOKEN.")
    os.environ["HF_WRITE_TOKEN"] = out
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument(
        "--no-wait",
        action="store_true",
        help="Fire the rebuild and return without polling.",
    )
    ap.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Max seconds to wait for build (default: 900).",
    )
    args = ap.parse_args()

    try:
        from huggingface_hub import HfApi  # type: ignore
    except ImportError:
        sys.exit("huggingface_hub not installed. pip install huggingface_hub")

    token = ensure_token()
    api = HfApi(token=token)

    print(f"Triggering factory reboot of space {args.repo} ...")
    api.restart_space(args.repo, factory_reboot=True)

    if args.no_wait:
        print("Reboot signaled. Not waiting for build (--no-wait).")
        print(f"Watch progress at: https://huggingface.co/spaces/{args.repo}/logs")
        return

    print("Polling build status (every 15s)...")
    last = None
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        info = api.space_info(args.repo)
        stage = info.runtime.stage
        if stage != last:
            elapsed = int(args.timeout - (deadline - time.time()))
            print(f"  t={elapsed}s stage={stage}")
            last = stage
        if stage in ("RUNNING", "RUNNING_BUILDING"):
            print(f"\nSpace is live: https://{args.repo.replace('/', '-')}.hf.space/")
            return
        if stage in ("BUILD_ERROR", "RUNTIME_ERROR"):
            print(f"\nFailed: stage={stage}")
            print(f"Logs: https://huggingface.co/spaces/{args.repo}/logs")
            sys.exit(1)
        time.sleep(15)

    print(f"\nTimeout after {args.timeout}s (still {last}).")
    print(f"Logs: https://huggingface.co/spaces/{args.repo}/logs")
    sys.exit(2)


if __name__ == "__main__":
    main()
