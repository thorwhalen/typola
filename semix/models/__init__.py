"""Probabilistic models over a `Typology`.

Components
----------

- `Distribution` — a single categorical distribution with counts, probabilities,
  support labels, entropy, and top-k methods.
- `Marginal`     — builds a `Distribution` for P(parameter value | condition),
  using a user-specified estimator.
- `Conditional`  — builds a CPT: for every value of a "given" parameter,
  a `Distribution` over a "target" parameter.
"""
from semix.models.distribution import Distribution
from semix.models.marginal import Marginal
from semix.models.conditional import Conditional

__all__ = ["Distribution", "Marginal", "Conditional"]
