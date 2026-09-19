#!/usr/bin/env python3
"""update-hf-space-webapp.py — push webapp/api + UI dist to the HF Space.

WHY THIS EXISTS:
    The PyPI wheel only ships the `typola/` package — webapp/api/ and
    webapp/ui/ live separately in the HF Space repo. Whenever you change
    those locally, you have to push them to the Space too.

    We can't build the UI inside Docker because webapp/ui/package-lock.json
    has `file:` dependencies to a local zodal monorepo that doesn't exist
    on the Space build machine. So we build dist/ locally and ship it.

WHAT IT DOES:
    1. cd webapp/ui && npm run build  (rebuilds dist/ from current source)
    2. Stage Dockerfile + README + webapp/api/ + webapp/ui/dist/ in /tmp/typola-space/
    3. upload_folder to thorwhalen/typola Space (replaces the live files)
    4. Trigger a factory reboot so the new files are picked up

ASSUMPTIONS:
    - Run from anywhere (script cd's to the typola repo).
    - HF_WRITE_TOKEN env var or ~/.keys has it.
    - npm + node installed locally.
    - /tmp/typola-space/ may exist from a prior run; it's reused.

USAGE:
    python update-hf-space-webapp.py                  # full cycle
    python update-hf-space-webapp.py --skip-build     # if dist/ already fresh
    python update-hf-space-webapp.py --no-restart     # upload only, no reboot
"""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys

# This script lives at <repo>/skills/typola-dev/scripts/, so the repo root is
# three levels up. Override with TYPOLA_REPO_DIR when running it from elsewhere.
REPO_DIR = pathlib.Path(
    os.environ.get("TYPOLA_REPO_DIR")
    or pathlib.Path(__file__).resolve().parents[3]
)
STAGING_DIR = pathlib.Path("/tmp/typola-space")
DEFAULT_SPACE = "thorwhalen/typola"
KEYS_FILE = pathlib.Path.home() / ".keys"


def ensure_token() -> str:
    tok = os.environ.get("HF_WRITE_TOKEN")
    if tok:
        return tok
    if not KEYS_FILE.is_file():
        sys.exit(f"HF_WRITE_TOKEN not set and {KEYS_FILE} does not exist.")
    out = subprocess.run(
        ["bash", "-c", f"source {KEYS_FILE} && printf '%s' \"$HF_WRITE_TOKEN\""],
        capture_output=True, text=True, check=True,
    ).stdout
    if not out:
        sys.exit("~/.keys does not export HF_WRITE_TOKEN.")
    os.environ["HF_WRITE_TOKEN"] = out
    return out


def build_ui() -> None:
    ui_dir = REPO_DIR / "webapp" / "ui"
    print(f"Building UI in {ui_dir} ...")
    subprocess.run(["npm", "run", "build"], cwd=ui_dir, check=True)
    print("UI build complete.")


def stage(dockerfile_pin: str | None) -> None:
    """Lay out the Space repo's contents in STAGING_DIR.

    Reuses what's already there for things we don't change (Dockerfile,
    README); overwrites webapp/api/ and webapp/ui/dist/ with the latest.
    """
    api_src = REPO_DIR / "webapp" / "api"
    dist_src = REPO_DIR / "webapp" / "ui" / "dist"

    if not api_src.is_dir():
        sys.exit(f"Missing source: {api_src}")
    if not dist_src.is_dir():
        sys.exit(f"Missing build output: {dist_src} (run with build, or rebuild manually).")

    STAGING_DIR.mkdir(exist_ok=True)
    (STAGING_DIR / "webapp").mkdir(exist_ok=True)

    # Copy webapp/api/ (replace).
    api_dst = STAGING_DIR / "webapp" / "api"
    if api_dst.exists():
        shutil.rmtree(api_dst)
    shutil.copytree(api_src, api_dst)

    # Copy webapp/ui/dist/ (replace, but keep the parent ui/ dir clean).
    ui_dst = STAGING_DIR / "webapp" / "ui"
    if ui_dst.exists():
        shutil.rmtree(ui_dst)
    ui_dst.mkdir()
    shutil.copytree(dist_src, ui_dst / "dist")

    # Make sure Dockerfile + README exist; if not, create minimal versions.
    dockerfile = STAGING_DIR / "Dockerfile"
    if not dockerfile.exists():
        dockerfile.write_text(_default_dockerfile(dockerfile_pin or "~=0.1.1"))
        print(f"Created default Dockerfile (pin: {dockerfile_pin or '~=0.1.1'})")
    elif dockerfile_pin:
        # Update the pin in place.
        text = dockerfile.read_text()
        import re
        new_text = re.sub(
            r'"typola\[web\][^"]*"',
            f'"typola[web]{dockerfile_pin}"',
            text,
        )
        if new_text != text:
            dockerfile.write_text(new_text)
            print(f"Updated Dockerfile pin → typola[web]{dockerfile_pin}")

    readme = STAGING_DIR / "README.md"
    if not readme.exists():
        readme.write_text(_default_readme())
        print("Created default README.md (with HF YAML frontmatter)")

    gitignore = STAGING_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("__pycache__/\n*.py[cod]\nnode_modules/\n.DS_Store\n")


def _default_dockerfile(pin: str) -> str:
    return f"""FROM python:3.12-slim
WORKDIR /app

# Install typola from PyPI ({pin}).
RUN pip install --no-cache-dir "typola[web]{pin}"

# FastAPI app source + prebuilt React UI.
COPY webapp/api/ /app/webapp/api/
COPY webapp/ui/dist/ /app/webapp/ui/dist/

# Pre-cache CLDF datasets so cold start is sub-second.
ENV TYPOLA_DATA_DIR=/app/data
RUN python -c "from typola import load; load('wals'); load('grambank')"

EXPOSE 7860
CMD ["uvicorn", "webapp.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
"""


def _default_readme() -> str:
    return """---
title: Typola
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Typola

Probabilistic models over linguistic typology data (WALS, Grambank, ...).

- Source: https://github.com/thorwhalen/typola
- Package: https://pypi.org/project/typola/
"""


def upload(token: str, space: str, message: str) -> None:
    from huggingface_hub import HfApi
    api = HfApi(token=token)
    print(f"Uploading {STAGING_DIR} to space {space} ...")
    api.upload_folder(
        folder_path=str(STAGING_DIR),
        repo_id=space,
        repo_type="space",
        commit_message=message,
        ignore_patterns=["node_modules/**", "__pycache__/**", "*.pyc", ".DS_Store"],
    )
    print("Upload complete.")


def restart(token: str, space: str) -> None:
    from huggingface_hub import HfApi
    api = HfApi(token=token)
    print(f"Triggering factory reboot of {space} ...")
    api.restart_space(space, factory_reboot=True)
    print(f"Reboot signaled. Logs: https://huggingface.co/spaces/{space}/logs")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--space", default=DEFAULT_SPACE)
    ap.add_argument("--skip-build", action="store_true",
                    help="Don't rebuild dist/; use what's already there.")
    ap.add_argument("--no-restart", action="store_true",
                    help="Upload only; skip the factory reboot.")
    ap.add_argument("--pin", help='Override the Dockerfile typola pin (e.g. "~=0.2.0").')
    ap.add_argument("--message", default="Update webapp source",
                    help="Commit message for the Space repo.")
    args = ap.parse_args()

    token = ensure_token()

    if not args.skip_build:
        build_ui()

    stage(args.pin)
    upload(token, args.space, args.message)

    if not args.no_restart:
        restart(token, args.space)
        print(f"\nWatch progress: scripts/rebuild-hf-space.py --no-wait (or polling)")


if __name__ == "__main__":
    main()
