---
name: typola-dev
description: Typola-specific operational know-how — publishing new versions of typola to PyPI, refreshing or updating the Hugging Face Space (thorwhalen-typola.hf.space), the typola Dockerfile pin convention, and the CLDF source URL pattern in typola/sources/catalog.py. Use this skill whenever the user works inside the typola repository or asks about "publishing typola", "updating typola space", "rebuilding typola space", "typola release", "typola maintenance", or "typola webapp". For the wads CI auto-bump push-back / version-sync issue (which is universal to wads-managed repos, not typola-specific), see the wads-ci-fix skill. For HF Space deploys in general (not just typola), see the hf-space-deploy skill in hfdol.
---

# typola-dev

Typola-specific maintenance know-how. The **typola** Python package is published to PyPI, mirrored on GitHub, served as a HuggingFace Space, and reverse-proxied at apps.thorwhalen.com/typola/.

## Cross-skill responsibilities

This skill is intentionally narrow. For broader concerns, defer to:

| Concern | Skill |
|---|---|
| wads CI auto-bump push-back fails / PyPI ahead of local pyproject.toml | **`wads-ci-fix`** |
| Generic HF Space deploy patterns (any package, not just typola) | **`hf-space-deploy`** (in hfdol) |
| Reverse-proxy wiring of typola in tw_platform | **`twp-config`** + **`extract-app`** (in tw_platform) |

This skill keeps only what's specific to typola.

## Where things live

| Resource | Location |
|---|---|
| Source repo | this repository (the skill lives in its `skills/` directory) |
| Package code | `typola/` (sources, prep, estimators, models, query subpackages) |
| Webapp backend | `webapp/api/` (FastAPI, served at `/api/*`) |
| Webapp frontend | `webapp/ui/` (React + Vite + shadcn, served at `/`) |
| Tests | `tests/` (94 cases; uses `/api/` prefix for HTTP tests) |
| GitHub | https://github.com/thorwhalen/typola |
| PyPI | https://pypi.org/project/typola/ |
| HF Space (live UI) | https://thorwhalen-typola.hf.space/ |
| HF Space repo | https://huggingface.co/spaces/thorwhalen/typola (Docker SDK, port 7860) |

The package was renamed from **semix → typola** on 2026-04-30; the local directory was renamed shortly after. Anywhere a stale reference shows up (e.g., a path or import still naming `semix`), update to `typola`.

## Decision tree: what task are you doing?

| You want to... | Read |
|---|---|
| Publish a new version of typola (any code change) | "Publishing a new version" below |
| Trigger an HF Space rebuild that just refreshes the typola lib | `scripts/rebuild-hf-space.py` (or use `hfdol.deploy.factory_reboot`) |
| Push webapp/api/ or webapp/ui/ changes to the HF Space | `scripts/update-hf-space-webapp.py` (or use `hfdol.deploy.deploy_webapp`) |
| Bump the typola version pin in the HF Space's Dockerfile (e.g., 0.1.x → 0.2.x) | "Bumping the major/minor pin" below |
| Add or fix a CLDF source URL | "CLDF source URL pattern" below |
| Sync pyproject.toml after CI auto-bumped PyPI | **wads-ci-fix** skill (`scripts/sync-pypi-version.sh --package typola --repo-dir .`) |
| Permanently fix the CI auto-bump push-back | **wads-ci-fix** skill (`scripts/setup-ssh-deploy-key.sh --repo thorwhalen/typola`) |

## Publishing a new version

The CI on every merge to `main` auto-bumps the version, publishes to PyPI, then **fails** to push the bump back (no SSH key set). Until that's fixed permanently (see `wads-ci-fix`'s `setup-ssh-deploy-key.sh`), the routine is:

1. Edit code, make sure tests pass: `pytest -x -q`
2. Format + lint to keep CI happy: `uvx ruff format . && uvx ruff check typola`
3. Commit and push to `main`. CI publishes the bumped version to PyPI.
4. After CI finishes, run `wads-ci-fix`'s sync:
   ```bash
   bash ~/.claude/skills/wads-ci-fix/scripts/sync-pypi-version.sh \
     --package typola --repo-dir .
   ```

The simpler long-term fix is `wads-ci-fix`'s `setup-ssh-deploy-key.sh --repo thorwhalen/typola` — once SSH push-back works, steps 3 and 4 collapse into "just push, CI handles everything."

If your change requires the HF Space to re-pull the new typola from PyPI, also run `scripts/rebuild-hf-space.py` (or `hfdol.deploy.factory_reboot("thorwhalen/typola")`). The Space's Dockerfile pin is a compatible-release spec (`~=0.1.1`), so it auto-picks up `0.1.x` patches but not `0.2.0`.

## Bumping the major/minor pin

The HF Space pins `typola[web]~=0.1.1` in its Dockerfile, which allows `0.1.x` patches but blocks `0.2.0`. To move to a new minor:

1. Edit `/tmp/typola-space/Dockerfile`: change the version spec.
2. Re-upload and rebuild via `scripts/update-hf-space-webapp.py` (or use the generic `hf-space-deploy` skill — same operation, just typola-defaults baked in here).
3. Verify the new version landed: `curl -s https://thorwhalen-typola.hf.space/api/typologies` should still return the typology list.

Don't pin too loosely (e.g., `>=0.1.0`) — Docker layer caching means `pip install` doesn't rerun automatically when PyPI gets a new version, but more importantly the bundled webapp/api/ + dist/ might encode an older API contract. Pin to a compatible-release range, bump deliberately.

## CLDF source URL pattern

The package's data-source URLs live in `typola/sources/catalog.py`. Zenodo's URLs occasionally change (the `record/` → `records/` migration; filename versions like `v1.0.zip` vs `v1.0.3.zip`). When a download fails:

1. Curl the URL with `-sIL` to see what status + redirects you get.
2. Hit Zenodo's API: `curl -s "https://zenodo.org/api/records/<RECORD_ID>"` → look at the `files` array for the canonical `key` and `links.self`.
3. Patch the URL in `catalog.py`, run tests (those don't network — but you can `python -c "from typola import load; load('grambank')"` to verify), commit, push. CI will publish a patch version.

The grambank URL was wrong in 0.1.1 — fixed in 0.1.2 (record `7740140`, file `grambank/grambank-v1.0.zip`, not `v1.0.3.zip`).

## Known gotchas

These are real bugs we've hit, not theoretical ones. Reading them first will save you 15 minutes each.

### 1. Webapp UI lockfile has `file:` deps to your local zodal monorepo

`webapp/ui/package-lock.json` references `@zodal/core`, `@zodal/store`, `@zodal/store-localstorage` as `file:../../../../i/_zodals/...`. Those paths only exist on this machine. **Never run `npm ci` on a clean machine** (HF Space build, CI, a new clone) — it'll fail with an opaque "lockfileVersion" error that's actually about the unresolvable `file:` deps.

**Implication for the HF Space**: don't try a multi-stage Dockerfile that does `npm ci`. Instead, build `dist/` locally (`cd webapp/ui && npm run build`) and ship it as-is. That's what `scripts/update-hf-space-webapp.py` does (and what `hfdol.deploy.stage_webapp()` expects).

### 2. Skipping CI

To push a commit that should not trigger CI (e.g., the post-publish version sync), include `[skip ci]` anywhere in the commit message. Without it, you can get into a publish loop where CI re-publishes the same version and fails on duplicate.

### 3. API path prefix

`webapp/api/main.py` mounts API endpoints under `/api/*` (so the SPA at `/` and the API can share an origin without route collisions). Tests in `tests/test_api.py` use the `/api/` prefix. **If you add a new endpoint, prefix its path with `/api/`** — otherwise the SPA's `lib/api.ts` won't find it (it defaults `VITE_API_BASE` to `api`, relative — see gotcha #6).

### 6. Frontend uses RELATIVE base paths — don't change to absolute

`vite.config.ts` defaults `base` to `"./"` and `src/lib/api.ts` defaults `API_BASE` to `"api"` (no leading slash). This is intentional: it lets a **single build** serve correctly both at the HF Space root (`thorwhalen-typola.hf.space/`) AND under the tw_platform reverse proxy (`apps.thorwhalen.com/typola/`). Without this, the proxied URL would silently 404 on `/assets/...` (white page) because the browser would resolve absolute `/assets/...` against `apps.thorwhalen.com/` instead of `apps.thorwhalen.com/typola/`.

If you find yourself changing those defaults back to `"/"` and `"/api"`, **stop** — the proxy will break. The current setup relies on `document.baseURI` resolution. Safe because typola has no client-side routing (no `react-router`, no `pushState`); if you add routing, switch API_BASE to be computed once at startup from `document.baseURI` (see the extract-app skill's gotcha 4b for the rationale).

Symptom of regression: `curl -s https://apps.thorwhalen.com/typola/` shows `src="/assets/..."` (absolute) instead of `src="./assets/..."` (relative). Fix: confirm `vite.config.ts` has `base: PUBLIC_BASE` with `PUBLIC_BASE` defaulting to `"./"`, rebuild (`npm run build` in `webapp/ui/`), and redeploy the HF Space.

### 4. `webapp/` is NOT in the wheel

The PyPI wheel only ships the `typola/` package directory. The webapp lives separately in two places: this repo (source-of-truth for editing) and the HF Space repo (where it actually runs). When you change webapp code, you have to push it to **both** — the typola repo (commit + push) AND the HF Space (via `scripts/update-hf-space-webapp.py`).

### 5. HF Space token must be a write token

The session-default `HF_TOKEN` may be a read-only token. Write operations (create_repo, upload_folder, restart_space) need a write token; the convention is `HF_WRITE_TOKEN` in `~/.keys`. The `hfdol.deploy.ensure_write_token()` helper handles the resolution.

## Auxiliary state to know about

- **Stash@{0} in the typola repo**: `WIP: refactor app.toml + add server.py (for typola rename in separate session)`. This was deferred deploy plumbing for tw_platform. **Likely obsolete now** — the chosen approach is `mode = "external"` in tw_platform's app.toml, which doesn't need the server.py shim. Confirm with the user before dropping the stash; the tw_platform session may want to inspect it.

- **`HF_WRITE_TOKEN` env var**: kept in `~/.keys`. To make it available, run `source ~/.keys` (or have scripts source it themselves).

- **The cancellation pattern**: if you accidentally push a commit to `main` that triggers a needless CI publish (e.g., a doc-only change with no library changes), cancel it with `gh run cancel <RUN_ID> -R thorwhalen/typola` before it bumps the version. Saves a sync round-trip.

## Scripts

The two typola-specific scripts that remain. The wads-CI scripts (`sync-pypi-version.sh`, `setup-ssh-deploy-key.sh`) live in the **`wads-ci-fix`** skill — they apply to every wads-managed repo, not just typola.

| Script | Purpose |
|---|---|
| `scripts/rebuild-hf-space.py` | Trigger an HF Space rebuild (`factory_reboot=True` busts the Docker layer cache). Use after publishing a new typola version that the Space should pick up. Equivalent to `python -c 'from hfdol.deploy import factory_reboot; factory_reboot("thorwhalen/typola")'`. |
| `scripts/update-hf-space-webapp.py` | Build the UI locally + reupload `webapp/api/` and `webapp/ui/dist/` to the HF Space + restart. Use whenever webapp source changes. Equivalent to using `hfdol.deploy.deploy_webapp` with typola defaults. |

Each script prints what it's about to do before doing it, and prompts for confirmation on destructive or hard-to-undo steps (git push, secret upload, factory reboot).
