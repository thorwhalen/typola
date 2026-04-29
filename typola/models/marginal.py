"""Marginal distribution over a parameter's support, under a condition."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from typola.estimators import Estimator, jeffreys
from typola.models.distribution import Distribution
from typola.prep.canonical import Typology


class Marginal:
    """Build a `Distribution` over one parameter's values.

    This is the entry point for ``P(parameter value | condition)``. The
    condition is any filter on language metadata columns (see
    `Typology.filter_languages`). The count→probability strategy is
    specified by ``estimator``.

    Example
    -------
    >>> from typola import load, estimators
    >>> from typola.models import Marginal
    >>> wals = load("wals")
    >>> dist = Marginal(
    ...     wals, "81A",
    ...     condition={"Family": "Austronesian"},
    ...     estimator=estimators.laplace(0.5),
    ... ).distribution
    >>> dist.top_k(3)
    """

    def __init__(
        self,
        typology: Typology,
        parameter: str,
        *,
        condition: Optional[Mapping[str, Any]] = None,
        parameter_conditions: Optional[Mapping[str, Any]] = None,
        estimator: Optional[Estimator] = None,
        drop_missing: bool = True,
    ):
        self.typology = typology
        self.parameter = parameter
        self.condition = dict(condition) if condition else {}
        self.parameter_conditions = (
            dict(parameter_conditions) if parameter_conditions else {}
        )
        self.estimator = estimator or jeffreys()
        self.drop_missing = drop_missing

        self.parameter_id = typology.parameter_id(parameter)
        self.counts = typology.counts(
            self.parameter_id,
            condition=self.condition,
            parameter_conditions=self.parameter_conditions,
            drop_missing=self.drop_missing,
        )
        if self.counts.sum() == 0 and self.estimator.name == "mle":
            raise ValueError(
                f"No observations for parameter {parameter!r} under condition "
                f"{self.condition!r}, and MLE is undefined. Use a smoothing "
                f"estimator (laplace, jeffreys, dirichlet, empirical_bayes)."
            )
        self.probabilities = self.estimator(self.counts)
        self.labels = typology.code_labels(self.parameter_id)

    @property
    def distribution(self) -> Distribution:
        return Distribution(
            probabilities=self.probabilities,
            counts=self.counts,
            support_labels=self.labels,
            estimator_name=self.estimator.name,
            metadata={
                "typology": self.typology.name,
                "parameter_id": self.parameter_id,
                "parameter_name": str(
                    self.typology.parameters.loc[self.parameter_id].get("Name", "")
                ),
                "condition": self.condition,
                "parameter_conditions": self.parameter_conditions,
                "estimator_params": dict(self.estimator.params),
            },
        )
