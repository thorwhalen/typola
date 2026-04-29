"""Tests for the high-level query API."""
from __future__ import annotations

import pandas as pd
import pytest

from typola import estimators, query
from typola.models import Conditional, Distribution
from typola.query import (
    compare_conditions,
    compare_estimators,
    cross_validate_estimators,
    rank_associations,
)


# ---------- query() entry-point branching -----------------------------------


def test_query_marginal(toy_typology):
    result = query(toy_typology, target="SV_order", estimator=estimators.mle())
    assert isinstance(result, Distribution)
    assert result.mode() == "P1-1"


def test_query_conditional_full_cpt(toy_typology):
    result = query(toy_typology, target="Tone", given="SV_order",
                   estimator=estimators.laplace(0.5))
    assert isinstance(result, Conditional)
    # Each row sums to 1
    assert result.as_matrix().sum(axis=1).round(8).eq(1.0).all()


def test_query_conditional_with_value(toy_typology):
    result = query(toy_typology, target="Tone", given="SV_order",
                   given_value="P1-1", estimator=estimators.mle())
    assert isinstance(result, Distribution)
    # SV=P1-1 has three languages a,b,d with tone codes each unique
    assert len(result.support) == 3


def test_query_with_language_condition(toy_typology):
    result = query(
        toy_typology, target="SV_order",
        condition={"Family": "F1"},
        estimator=estimators.laplace(1.0),
    )
    # F1 has 2 SV, 0 VS; laplace(1) → 3/4, 1/4
    assert abs(result.probabilities["P1-1"] - 0.75) < 1e-9


# ---------- compare / evaluate utilities -------------------------------------


def test_compare_estimators_returns_one_column_per_estimator(toy_typology):
    frame = compare_estimators(
        toy_typology, target="SV_order",
        estimators=[
            estimators.mle(),
            estimators.laplace(0.5),
            estimators.laplace(1.0),
            estimators.empirical_bayes([50, 50], strength=5.0),
        ],
    )
    # Expected columns include all four estimator names
    for col in ["mle", "laplace", "empirical_bayes"]:
        assert any(col in c for c in frame.columns)


def test_compare_conditions_global_and_named(toy_typology):
    frame = compare_conditions(
        toy_typology,
        target="SV_order",
        conditions={"F1_only": {"Family": "F1"}, "F2_only": {"Family": "F2"}},
        estimator=estimators.laplace(0.5),
    )
    assert "overall" in frame.columns
    assert "F1_only" in frame.columns
    assert "F2_only" in frame.columns


def test_cross_validate_estimators_ranks_them(toy_typology):
    # With a toy set this is essentially a smoke test — just needs to run
    # and return a DataFrame with expected columns.
    df = cross_validate_estimators(
        toy_typology, target="Tone",
        estimators=[estimators.laplace(1.0), estimators.jeffreys()],
        n_folds=2,
        random_state=42,
    )
    assert "log_likelihood" in df.columns
    assert len(df) == 2


# ---------- real WALS ---------------------------------------------------------


def test_wals_rank_associations_top_of_81A_is_related(wals):
    df = rank_associations(
        wals, target="81A",
        top_k=5, estimator=estimators.laplace(0.5), min_observations=200,
    )
    # Top associations with Subject-Verb order should include other word-order
    # features. 83A (Object-Verb) is the canonical high-MI partner.
    top_ids = df["parameter_id"].tolist()
    assert "83A" in top_ids


def test_wals_cross_validated_smoothing_beats_mle_for_small_conditions(wals):
    # Austronesian is smaller than the whole world; unseen codes more common.
    df = cross_validate_estimators(
        wals, target="81A",
        estimators=[estimators.mle(), estimators.laplace(0.5), estimators.jeffreys()],
        n_folds=5, random_state=0,
        condition={"Family": "Austronesian"},
    )
    # Laplace/Jeffreys should beat MLE in log-likelihood
    mle_row = df[df.index.str.startswith("mle")]
    assert mle_row["log_likelihood"].iloc[0] < df["log_likelihood"].max()
