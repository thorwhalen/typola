"""A categorical distribution over a known support, with introspection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class Distribution:
    """A categorical probability distribution with provenance.

    Attributes
    ----------
    probabilities : pd.Series
        Non-negative, sums to 1. Index labels the support (typically code IDs).
    counts : pd.Series
        Raw counts this distribution was built from; same index as probabilities.
    support_labels : pd.Series
        Human-readable name for each support element (e.g. "SVO"), same index.
    estimator_name : str
        The estimator used ("mle", "laplace", etc.); useful in comparisons.
    metadata : dict
        Freeform: parameter id, condition, source, etc.
    """

    probabilities: pd.Series
    counts: pd.Series
    support_labels: Optional[pd.Series] = None
    estimator_name: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        p_sum = float(self.probabilities.sum())
        if not np.isclose(p_sum, 1.0, atol=1e-8):
            raise ValueError(
                f"Distribution.probabilities must sum to 1 (got {p_sum:.6f})"
            )

    # ----- basic intro --------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Distribution(n={len(self.probabilities)}, "
            f"estimator={self.estimator_name!r}, "
            f"n_obs={int(self.counts.sum())}, "
            f"H={self.entropy():.3f} bits)"
        )

    @property
    def support(self) -> list:
        return list(self.probabilities.index)

    @property
    def n_observations(self) -> int:
        return int(self.counts.sum())

    # ----- information-theoretic measures -------------------------------------

    def entropy(self, *, base: float = 2.0) -> float:
        """Shannon entropy of the probability vector (default: bits)."""
        p = self.probabilities.to_numpy(dtype=float)
        p_safe = p[p > 0]
        return float(-np.sum(p_safe * np.log(p_safe)) / np.log(base))

    def normalized_entropy(self, *, base: float = 2.0) -> float:
        """Entropy / log(K): 1 = uniform, 0 = point mass."""
        k = len(self.probabilities)
        if k <= 1:
            return 0.0
        return self.entropy(base=base) / (np.log(k) / np.log(base))

    def mode(self):
        """Return the label of the most probable support element."""
        return self.probabilities.idxmax()

    # ----- top-k / display ----------------------------------------------------

    def top_k(self, k: int = 5) -> pd.DataFrame:
        """Return the k most probable outcomes as a DataFrame."""
        ranked = self.probabilities.sort_values(ascending=False).head(k)
        return self.to_frame().loc[ranked.index]

    def to_frame(self) -> pd.DataFrame:
        """One row per support element with columns: name, count, probability."""
        frame = pd.DataFrame(
            {
                "count": self.counts.reindex(self.probabilities.index).fillna(0).astype(int),
                "probability": self.probabilities,
            }
        )
        if self.support_labels is not None:
            frame.insert(
                0, "name", self.support_labels.reindex(self.probabilities.index)
            )
        return frame

    # ----- sampling -----------------------------------------------------------

    def sample(self, n: int = 1, rng: Optional[np.random.Generator] = None) -> list:
        """Sample n outcomes from the distribution."""
        if rng is None:
            rng = np.random.default_rng()
        indices = rng.choice(
            len(self.probabilities),
            size=n,
            p=self.probabilities.to_numpy(dtype=float),
        )
        return [self.support[i] for i in indices]

    # ----- information-theoretic comparisons ---------------------------------

    def kl_divergence(self, other: "Distribution", *, eps: float = 1e-12) -> float:
        """KL(self || other), requires compatible supports."""
        from typola.estimators.base import kl_divergence

        aligned = other.probabilities.reindex(self.probabilities.index).fillna(eps)
        return kl_divergence(self.probabilities, aligned, eps=eps)
