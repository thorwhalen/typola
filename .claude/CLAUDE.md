# typola

Probabilistic models over linguistic typology source data (WALS, Grambank, ...):
load a typology, query conditional/marginal/joint distributions over feature codes,
with pluggable smoothing estimators. Ships as a PyPI package, a FastAPI+React webapp
(deployed as a HuggingFace Space and reverse-proxied at apps.thorwhalen.com/typola/),
and a `typola-dev` maintenance skill.

## Module map

- `typola/sources/` — describe & acquire raw CLDF typology datasets (`catalog.py`
  holds the source URL patterns).
- `typola/prep/` — parse raw CLDF into a canonical `Typology` (`canonical.py`,
  `cldf.py`, `loaders.py`, `stores.py`).
- `typola/estimators/` — count-to-probability strategies (MLE, Laplace, Jeffreys) —
  `base.py` defines the pluggable interface, `smoothing.py` the implementations.
- `typola/models/` — probabilistic models: `marginal.py`, `conditional.py`,
  `distribution.py`.
- `typola/query/` — the high-level `query()` / drill-down API (`api.py`).
- `webapp/api/` — FastAPI app (`main.py`, `app_attr = "app"`); `schemas.py`,
  `deps.py`. **Not covered by the package's ruff lint scope** (see below).
- `webapp/ui/` — React/Vite/Tailwind frontend, built via `npm install && npm run build`.
- `app.toml` — the `enlace` app descriptor: entry point, frontend dir, and a
  proposed (not-yet-standard) `[build]` section the tw_platform deployer reads.

## Tests & lint (verified)

```bash
uv venv .venv && uv pip install -e ".[dev]"   # dev extra pulls in fastapi/httpx —
                                                # required for tests/test_api.py and
                                                # webapp/api/*.py doctest collection
.venv/bin/pytest        # 76 passed, 18 skipped locally
uvx ruff check typola tests   # matches the CI-intended scope
```
Or `wads ci-local` for the full gate (installer=uv, extras=dev, Python 3.10+3.12, no
Windows job, no coverage — see `[tool.wads.ci]` in `pyproject.toml`).

**Gotchas found verifying:**
- `uv pip install -e .` alone (no `[dev]` extra) leaves fastapi/pydantic out; test
  collection then fails with `ModuleNotFoundError` on `webapp/api/*.py` — this
  already bit CI once (issue #3).
- `[tool.ruff.lint]` is a hand-pinned ruleset snapshot (not ruff's floating
  defaults) — see the long comment above it in `pyproject.toml` for how to refresh
  it deliberately. `webapp/` is intentionally excluded from that lint scope (a
  separate, not-yet-made decision — issue #3); `ruff check .` (whole repo) reports
  pre-existing findings there that are not regressions.

## Docs & skills

- `skills/typola-dev` (symlinked at `.claude/skills/typola-dev`) — typola-specific
  release/deploy/Space-refresh know-how; defers to `wads-ci-fix` and `hf-space-deploy`
  (in `hfdol`) for the generic parts.
- `webapp/README.md` — webapp-specific dev notes.

## Dependents

None recorded in the fleet dependency graph.
