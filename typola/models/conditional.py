"""Conditional distribution: P(target parameter | given parameter)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

import numpy as np
import pandas as pd

from typola.estimators import Estimator, jeffreys
from typola.models.distribution import Distribution
from typola.prep.canonical import Typology


class Conditional:
    """CPT for P(target | given), over languages of the typology.

    Each row is a value of the ``given`` parameter; the row is a
    `Distribution` over values of the ``target`` parameter, built from
    the joint count table by applying the estimator row-wise.

    The matrix form is also exposed as a DataFrame via `.as_matrix()`.

    Example
    -------
    >>> from typola import load, estimators
    >>> from typola.models import Conditional
    >>> wals = load("wals")
    >>> cpt = Conditional(wals, target="83A", given="82A",
    ...                   estimator=estimators.laplace(0.5))
    >>> cpt.as_matrix().head()         # rows = 82A codes, cols = 83A codes
    >>> cpt.p_given("82A-1").top_k(3)  # distribution over 83A when 82A=82A-1
    """

    def __init__(
        self,
        typology: Typology,
        target: str,
        given: str,
        *,
        condition: Optional[Mapping[str, Any]] = None,
        parameter_conditions: Optional[Mapping[str, Any]] = None,
        estimator: Optional[Estimator] = None,
        drop_missing: bool = True,
    ):
        self.typology = typology
        self.target = target
        self.given = given
        self.condition = dict(condition) if condition else {}
        self.parameter_conditions = (
            dict(parameter_conditions) if parameter_conditions else {}
        )
        self.estimator = estimator or jeffreys()
        self.drop_missing = drop_missing

        self.target_id = typology.parameter_id(target)
        self.given_id = typology.parameter_id(given)
        # shape: (|given|, |target|) — rows = given values, cols = target values
        self.joint_counts: pd.DataFrame = typology.joint_counts(
            self.given_id,
            self.target_id,
            condition=self.condition,
            parameter_conditions=self.parameter_conditions,
            drop_missing=self.drop_missing,
        )
        self._build_cpt()

    def _build_cpt(self) -> None:
        """Apply the estimator row-wise to produce the CPT."""
        probs = self.joint_counts.copy().astype(float)
        for row_id in probs.index:
            row = self.joint_counts.loc[row_id]
            probs.loc[row_id] = np.asarray(self.estimator(row.to_numpy()))
        self.cpt = probs  # rows sum to 1
        self.target_labels = self.typology.code_labels(self.target_id)
        self.given_labels = self.typology.code_labels(self.given_id)

    # ----- consumers ----------------------------------------------------------

    def as_matrix(self) -> pd.DataFrame:
        """CPT as a DataFrame (rows = given code, cols = target code)."""
        return self.cpt.copy()

    def p_given(self, given_value) -> Distribution:
        """Distribution over target values given ``given_value``."""
        if given_value not in self.cpt.index:
            raise KeyError(
                f"{given_value!r} not in {self.given} codes: {list(self.cpt.index)[:5]}..."
            )
        row_probs = self.cpt.loc[given_value]
        row_counts = self.joint_counts.loc[given_value]
        return Distribution(
            probabilities=row_probs,
            counts=row_counts,
            support_labels=self.target_labels,
            estimator_name=self.estimator.name,
            metadata={
                "typology": self.typology.name,
                "target_id": self.target_id,
                "given_id": self.given_id,
                "given_value": given_value,
                "condition": self.condition,
                "estimator_params": dict(self.estimator.params),
            },
        )

    def mutual_information(self, *, base: float = 2.0) -> float:
        """Pointwise MI I(target; given) in bits.

        Computed from the estimator-smoothed joint via row-normalized CPT and
        the corresponding marginal over ``given``. Useful for ranking which
        parameter pairs actually co-vary.
        """
        n_total = self.joint_counts.to_numpy().sum()
        if n_total == 0:
            return 0.0
        # p(given) from row sums of joint counts
        p_given = self.joint_counts.sum(axis=1).astype(float)
        p_given = p_given / p_given.sum() if p_given.sum() > 0 else p_given
        # joint P(target, given) = P(given) * P(target|given)  (using smoothed CPT)
        joint = self.cpt.multiply(p_given, axis=0).to_numpy()
        p_target = joint.sum(axis=0)
        p_target = p_target / p_target.sum() if p_target.sum() > 0 else p_target

        mi = 0.0
        for i, pg in enumerate(p_given):
            for j, pt in enumerate(p_target):
                pij = joint[i, j]
                if pij > 0 and pg > 0 and pt > 0:
                    mi += pij * (np.log(pij / (pg * pt)) / np.log(base))
        return float(mi)
