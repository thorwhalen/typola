"""Estimator base class + evaluation utilities.

An estimator is just a callable ``counts -> probabilities`` with a name
and a params dict. Making it a small dataclass-like object (rather than
a bare function) lets us carry configuration, log runs reproducibly, and
build an evaluation harness that compares strategies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence, Union

import numpy as np
import pandas as pd

ArrayLike = Union[np.ndarray, pd.Series, Sequence[float]]


# ---------------------------------------------------------------------------
# the base abstraction
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Estimator:
    """Callable that maps count vectors to probability vectors.

    Subclasses override `_estimate(counts_array)` to return a numpy
    probability vector. The base class handles pandas-Series plumbing,
    normalization checks, and the `describe()` / `__repr__` machinery.
    """

    name: str = "estimator"
    params: Mapping = field(default_factory=dict)

    # subclasses implement this
    def _estimate(self, counts: np.ndarray) -> np.ndarray:  # pragma: no cover
        raise NotImplementedError

    def __call__(self, counts: ArrayLike) -> ArrayLike:
        arr = _to_array(counts)
        probs = self._estimate(arr)
        probs = np.asarray(probs, dtype=float)
        if probs.shape != arr.shape:
            raise ValueError(
                f"{self.name}: _estimate changed shape {arr.shape} → {probs.shape}"
            )
        if (probs < -1e-12).any():
            raise ValueError(f"{self.name}: produced negative probabilities")
        total = probs.sum()
        if total <= 0:
            raise ValueError(f"{self.name}: produced zero-mass distribution")
        # numerical cleanup
        probs = np.clip(probs, 0.0, None)
        probs = probs / probs.sum()
        return _wrap_like(probs, counts)

    def describe(self) -> dict:
        return {"name": self.name, **dict(self.params)}

    def __repr__(self) -> str:
        parts = []
        for k, v in self.params.items():
            if isinstance(v, np.ndarray):
                parts.append(f"{k}=array(len={len(v)})")
            elif isinstance(v, (list, tuple)) and len(v) > 4:
                parts.append(f"{k}={type(v).__name__}(len={len(v)})")
            else:
                parts.append(f"{k}={v!r}")
        return f"{self.name}({', '.join(parts)})"


# ---------------------------------------------------------------------------
# helpers that work on bare arrays (used by both estimators and evaluation)
# ---------------------------------------------------------------------------


def _to_array(x: ArrayLike) -> np.ndarray:
    if isinstance(x, pd.Series):
        return x.to_numpy(dtype=float)
    return np.asarray(x, dtype=float)


def _wrap_like(arr: np.ndarray, original: ArrayLike) -> ArrayLike:
    """Return ``arr`` wrapped in the type/index of ``original``."""
    if isinstance(original, pd.Series):
        return pd.Series(arr, index=original.index, name=original.name)
    return arr


def normalize(counts: ArrayLike) -> ArrayLike:
    """Divide by the sum so the result sums to 1. Raises if sum is 0."""
    arr = _to_array(counts)
    total = arr.sum()
    if total <= 0:
        raise ValueError("Cannot normalize a zero-mass count vector")
    return _wrap_like(arr / total, counts)


# ---------------------------------------------------------------------------
# evaluation: compare estimators on held-out data
# ---------------------------------------------------------------------------


def log_likelihood(p: ArrayLike, counts: ArrayLike, *, eps: float = 1e-12) -> float:
    """Log-likelihood of multinomial counts under distribution p.

    Returns ``sum(counts[i] * log(p[i]))`` ignoring the normalizing constant.
    Useful for comparing two estimators on the same held-out counts.
    """
    p_arr = _to_array(p)
    c_arr = _to_array(counts)
    p_safe = np.clip(p_arr, eps, None)
    return float(np.sum(c_arr * np.log(p_safe)))


def kl_divergence(p: ArrayLike, q: ArrayLike, *, eps: float = 1e-12) -> float:
    """KL(p || q) between two probability vectors."""
    p_arr = np.clip(_to_array(p), eps, None)
    q_arr = np.clip(_to_array(q), eps, None)
    return float(np.sum(p_arr * np.log(p_arr / q_arr)))


def held_out_score(
    estimator: Callable[[ArrayLike], ArrayLike],
    counts_train: ArrayLike,
    counts_test: ArrayLike,
) -> dict:
    """Fit an estimator on ``counts_train`` and score it on ``counts_test``.

    Returns a dict of metrics:

    - ``log_likelihood``  — higher is better
    - ``perplexity``      — exp(-log_likelihood / N_test); lower is better
    - ``kl_to_empirical`` — KL(empirical_test || predicted); 0 is perfect
    - ``name``            — estimator's reported name
    """
    p = estimator(counts_train)
    c_test = _to_array(counts_test)
    n_test = c_test.sum()
    ll = log_likelihood(p, c_test)
    name = getattr(estimator, "name", getattr(estimator, "__name__", "anonymous"))
    out = {"name": name, "log_likelihood": ll}
    if n_test > 0:
        out["perplexity"] = float(np.exp(-ll / n_test))
        emp = c_test / n_test
        out["kl_to_empirical"] = kl_divergence(emp, _to_array(p))
    return out
