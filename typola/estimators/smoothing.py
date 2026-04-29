"""Concrete count-to-probability estimators.

These implement the plug-and-play API described in ``typola.estimators``.
Each public function is a **factory** that returns an Estimator instance.
Instances are callables ``counts -> probabilities``.

Numerical notes
---------------
- All estimators are total-preserving: the output sums to 1 up to floating
  point. The base class re-normalizes defensively, but implementations
  already return clean normalized output.
- For an all-zero count vector (e.g. a parameter with no observations in the
  conditioning group), MLE raises. All Bayesian/smoothing estimators
  fall back to the prior. Use ``uniform()`` explicitly if you want strict
  uniform fallback.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from typola.estimators.base import ArrayLike, Estimator, _to_array

# ---------------------------------------------------------------------------
# MLE
# ---------------------------------------------------------------------------


@dataclass(frozen=True, repr=False)
class _MLE(Estimator):
    name: str = "mle"
    params: dict = field(default_factory=dict)

    def _estimate(self, counts: np.ndarray) -> np.ndarray:
        total = counts.sum()
        if total <= 0:
            raise ValueError(
                "MLE is undefined for an all-zero count vector. "
                "Use laplace(...), jeffreys(), or empirical_bayes(...) instead."
            )
        return counts / total


def mle() -> Estimator:
    """Raw relative frequencies. Zero probability for unobserved events."""
    return _MLE()


# ---------------------------------------------------------------------------
# Laplace / add-alpha
# ---------------------------------------------------------------------------


@dataclass(frozen=True, repr=False)
class _Laplace(Estimator):
    name: str = "laplace"
    params: dict = field(default_factory=dict)

    def _estimate(self, counts: np.ndarray) -> np.ndarray:
        alpha = float(self.params["alpha"])
        k = len(counts)
        smoothed = counts + alpha
        total = smoothed.sum()
        if total <= 0:
            # alpha=0 and all counts 0 → fall back to uniform
            return np.full(k, 1.0 / k)
        return smoothed / total


def laplace(alpha: float = 1.0) -> Estimator:
    """Add-alpha smoothing.

    alpha=1      → classic Laplace / add-one
    alpha=0.5    → Jeffreys prior (equivalent to `jeffreys()`)
    alpha=0      → MLE (but prefer `mle()` for clarity)
    """
    if alpha < 0:
        raise ValueError("alpha must be ≥ 0")
    return _Laplace(name="laplace", params={"alpha": float(alpha)})


def jeffreys() -> Estimator:
    """Jeffreys prior: symmetric Dirichlet with alpha_i = 0.5 for all i."""
    return _Laplace(name="jeffreys", params={"alpha": 0.5})


def uniform() -> Estimator:
    """Ignore counts; always return the uniform distribution over the support."""

    @dataclass(frozen=True, repr=False)
    class _Uniform(Estimator):
        name: str = "uniform"
        params: dict = field(default_factory=dict)

        def _estimate(self, counts: np.ndarray) -> np.ndarray:
            k = len(counts)
            return np.full(k, 1.0 / k)

    return _Uniform()


# ---------------------------------------------------------------------------
# Dirichlet-Multinomial (proper Bayesian posterior mean)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, repr=False)
class _Dirichlet(Estimator):
    name: str = "dirichlet"
    params: dict = field(default_factory=dict)

    def _estimate(self, counts: np.ndarray) -> np.ndarray:
        prior = _resolve_prior_vector(self.params["prior"], k=len(counts))
        posterior = counts + prior
        total = posterior.sum()
        if total <= 0:
            # everything zero → uniform
            k = len(counts)
            return np.full(k, 1.0 / k)
        return posterior / total


def dirichlet(prior: str | Sequence[float] | float = "jeffreys") -> Estimator:
    """Posterior mean under a Dirichlet prior.

    The prior vector is the expected pseudocount for each category.
    Posterior mean is ``(alpha_i + n_i) / sum(alpha + n)``.

    Parameters
    ----------
    prior :
        - ``"jeffreys"`` (default) — all 0.5
        - ``"uniform"`` — all 1.0 (Laplace)
        - ``"bayes_laplace"`` — alias for ``"uniform"``
        - a scalar — symmetric prior with that value
        - a sequence — per-category pseudocounts (length must match counts at call time)
    """
    return _Dirichlet(name="dirichlet", params={"prior": prior})


# ---------------------------------------------------------------------------
# Empirical Bayes — prior set from a global count vector
# ---------------------------------------------------------------------------


@dataclass(frozen=True, repr=False)
class _EmpiricalBayes(Estimator):
    name: str = "empirical_bayes"
    params: dict = field(default_factory=dict)

    def _estimate(self, counts: np.ndarray) -> np.ndarray:
        global_counts = np.asarray(self.params["global_counts"], dtype=float)
        if global_counts.shape != counts.shape:
            raise ValueError(
                f"empirical_bayes: global_counts shape {global_counts.shape} "
                f"does not match input counts shape {counts.shape}"
            )
        strength = float(self.params["strength"])
        # Build prior: global empirical distribution * strength (pseudocount mass)
        g_sum = global_counts.sum()
        if g_sum <= 0:
            # no global info — fall back to uniform
            prior = np.full_like(counts, strength / len(counts), dtype=float)
        else:
            prior = (global_counts / g_sum) * strength
        posterior = counts + prior
        total = posterior.sum()
        if total <= 0:
            k = len(counts)
            return np.full(k, 1.0 / k)
        return posterior / total


def empirical_bayes(
    global_counts: ArrayLike, *, strength: float = 1.0
) -> Estimator:
    """Smooth local counts toward a global empirical distribution.

    The prior is ``(global_counts / sum) * strength``. Think of ``strength``
    as the total pseudocount mass pulled from the global view.

    Typical use: smooth family-level counts toward the overall WALS
    distribution for that parameter.

    Parameters
    ----------
    global_counts :
        Count vector to use as the prior shape. Must have the same length as
        the local counts when the estimator is called.
    strength :
        Total pseudocount mass for the prior. Higher → more shrinkage toward
        the global. 0 recovers MLE (but will fail on zero-count cells — use
        `laplace(1e-6)` or similar as fallback).
    """
    g = np.asarray(_to_array(global_counts), dtype=float)
    return _EmpiricalBayes(
        name="empirical_bayes",
        params={"global_counts": g, "strength": float(strength)},
    )


# ---------------------------------------------------------------------------
# Mixture
# ---------------------------------------------------------------------------


@dataclass(frozen=True, repr=False)
class _Mixture(Estimator):
    name: str = "mix"
    params: dict = field(default_factory=dict)

    def _estimate(self, counts: np.ndarray) -> np.ndarray:
        components = self.params["components"]
        total_w = sum(w for w, _ in components)
        acc = np.zeros_like(counts, dtype=float)
        for w, est in components:
            probs = np.asarray(est(counts), dtype=float)
            acc += (w / total_w) * probs
        return acc


def mix(*components: tuple[float, Estimator]) -> Estimator:
    """Linear combination of estimators: `mix((0.7, laplace(1)), (0.3, mle()))`."""
    if not components:
        raise ValueError("mix() needs at least one (weight, estimator) pair")
    for w, _ in components:
        if w < 0:
            raise ValueError("mixture weights must be ≥ 0")
    return _Mixture(
        name="mix",
        params={
            "components": list(components),
            "summary": [(w, getattr(e, "name", repr(e))) for w, e in components],
        },
    )


# ---------------------------------------------------------------------------
# helper: resolve a prior specifier into a concrete vector
# ---------------------------------------------------------------------------


def _resolve_prior_vector(spec, *, k: int) -> np.ndarray:
    """Produce a length-k prior vector from a string / scalar / sequence."""
    if isinstance(spec, str):
        s = spec.lower()
        if s == "jeffreys":
            return np.full(k, 0.5)
        if s in ("uniform", "bayes_laplace", "laplace"):
            return np.full(k, 1.0)
        if s == "haldane":
            return np.full(k, 0.0)
        raise ValueError(f"Unknown prior spec {spec!r}")
    if np.isscalar(spec):
        return np.full(k, float(spec))
    vec = np.asarray(spec, dtype=float)
    if vec.ndim != 1 or len(vec) != k:
        raise ValueError(
            f"prior vector must be 1D of length {k}, got shape {vec.shape}"
        )
    if (vec < 0).any():
        raise ValueError("prior entries must be ≥ 0")
    return vec
