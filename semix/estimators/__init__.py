"""Pluggable count-to-probability estimators.

An *estimator* is a callable that converts a vector of non-negative counts
into a probability distribution (non-negative, sums to 1). The key idea
is that the count→probability step is swappable — so you can easily try
several strategies and test which works best for your task.

Canonical estimators
--------------------

- `mle`               — raw proportions (zero probability for unobserved events)
- `laplace(alpha)`    — add-alpha smoothing with a uniform pseudocount
- `jeffreys()`        — Laplace with alpha=0.5 (the Jeffreys-prior Dirichlet)
- `dirichlet(prior)`  — posterior mean under a configurable Dirichlet prior
- `empirical_bayes(global_counts, strength)` — prior built from global counts
- `mix(*(weight, est))` — linear combination of any number of estimators

All are pure callables that accept ``np.ndarray`` **or** ``pd.Series`` and
preserve the index of a Series. They all have a ``.name`` attribute and a
``.params`` dict so runs are self-describing.
"""
from semix.estimators.base import (
    Estimator,
    normalize,
    kl_divergence,
    log_likelihood,
    held_out_score,
)
from semix.estimators.smoothing import (
    mle,
    laplace,
    jeffreys,
    dirichlet,
    empirical_bayes,
    uniform,
    mix,
)

__all__ = [
    "Estimator",
    "normalize",
    "kl_divergence",
    "log_likelihood",
    "held_out_score",
    "mle",
    "laplace",
    "jeffreys",
    "dirichlet",
    "empirical_bayes",
    "uniform",
    "mix",
]
