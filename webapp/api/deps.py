"""Dependencies: typology cache + estimator factory.

The typology is loaded once per process and memoized. Tests can override the
path via the SEMIX_TYPOLOGY_<NAME>_PATH env vars.
"""
from __future__ import annotations

import os
from functools import lru_cache

from semix import Typology, estimators, load, load_from_cldf_dir

from webapp.api.schemas import EstimatorSpec


def _local_override(name: str) -> str | None:
    return os.environ.get(f"SEMIX_TYPOLOGY_{name.upper()}_PATH")


@lru_cache(maxsize=8)
def get_typology(name: str) -> Typology:
    """Load or reuse the cached typology for ``name`` (e.g. "wals")."""
    override = _local_override(name)
    if override:
        return load_from_cldf_dir(override, name=name)
    return load(name, verbose=False)


def build_estimator(spec: EstimatorSpec):
    """Construct a semix Estimator from a serializable EstimatorSpec."""
    name = spec.name
    params = spec.params or {}
    if name == "mle":
        return estimators.mle()
    if name == "laplace":
        return estimators.laplace(alpha=params.get("alpha", 1.0))
    if name == "jeffreys":
        return estimators.jeffreys()
    if name == "dirichlet":
        return estimators.dirichlet(prior=params.get("prior", "jeffreys"))
    if name == "empirical_bayes":
        # The frontend passes a typology + target reference; the server resolves
        # the global counts at query time (see main.py).
        raise ValueError(
            "empirical_bayes is resolved in main.py where global counts are known"
        )
    if name == "uniform":
        return estimators.uniform()
    raise ValueError(f"Unknown estimator {name!r}")
