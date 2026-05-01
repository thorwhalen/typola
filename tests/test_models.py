"""Tests for Marginal and Conditional models."""

from __future__ import annotations

import numpy as np
import pytest

from typola import estimators
from typola.models import Conditional, Distribution, Marginal


# ---------- Marginal ---------------------------------------------------------


def test_marginal_on_toy(toy_typology):
    m = Marginal(toy_typology, "SV_order", estimator=estimators.mle())
    dist = m.distribution
    assert isinstance(dist, Distribution)
    # MLE: 3 SV (P1-1), 1 VS (P1-2)
    assert np.isclose(dist.probabilities["P1-1"], 0.75)
    assert np.isclose(dist.probabilities["P1-2"], 0.25)
    assert dist.n_observations == 4


def test_marginal_with_condition(toy_typology):
    m = Marginal(
        toy_typology,
        "SV_order",
        condition={"Family": "F1"},
        estimator=estimators.laplace(1.0),
    )
    dist = m.distribution
    # F1 has 2 SV, 0 VS; laplace(1): (2+1)/(2+2)=3/4, (0+1)/4=1/4
    assert np.isclose(dist.probabilities["P1-1"], 0.75)
    assert np.isclose(dist.probabilities["P1-2"], 0.25)


def test_marginal_entropy_and_mode(toy_typology):
    dist = Marginal(toy_typology, "SV_order", estimator=estimators.mle()).distribution
    assert dist.mode() == "P1-1"
    # 75/25 split entropy ≈ 0.811 bits
    assert 0.7 < dist.entropy() < 0.9


def test_marginal_top_k_dataframe(toy_typology):
    dist = Marginal(
        toy_typology, "Tone", estimator=estimators.laplace(0.5)
    ).distribution
    df = dist.top_k(3)
    # top_k returns in descending probability order
    assert df["probability"].is_monotonic_decreasing


def test_marginal_no_observations_mle_errors(toy_typology):
    # Condition that matches no languages
    with pytest.raises(ValueError):
        Marginal(
            toy_typology,
            "SV_order",
            condition={"Family": "Z"},
            estimator=estimators.mle(),
        )


def test_marginal_no_observations_laplace_ok(toy_typology):
    m = Marginal(
        toy_typology,
        "SV_order",
        condition={"Family": "Z"},
        estimator=estimators.laplace(1.0),
    )
    # With alpha=1 and zero counts, falls back to uniform
    p = m.distribution.probabilities
    assert np.allclose(p.values, 0.5)


# ---------- Conditional ------------------------------------------------------


def test_conditional_rows_sum_to_one(toy_typology):
    cpt = Conditional(
        toy_typology, target="Tone", given="SV_order", estimator=estimators.laplace(0.5)
    )
    mat = cpt.as_matrix()
    row_sums = mat.sum(axis=1)
    for v in row_sums:
        assert np.isclose(v, 1.0)


def test_conditional_p_given_distribution(toy_typology):
    cpt = Conditional(
        toy_typology, target="Tone", given="SV_order", estimator=estimators.mle()
    )
    # When SV_order=P1-1 (3 langs a, b, d):
    #   a has Tone=P2-2, b=P2-3, d=P2-1 → each 1/3
    d = cpt.p_given("P1-1")
    assert np.isclose(d.probabilities["P2-1"], 1 / 3)
    assert np.isclose(d.probabilities["P2-2"], 1 / 3)
    assert np.isclose(d.probabilities["P2-3"], 1 / 3)


def test_conditional_mutual_information_is_non_negative(toy_typology):
    cpt = Conditional(
        toy_typology, target="Tone", given="SV_order", estimator=estimators.laplace(0.5)
    )
    assert cpt.mutual_information() >= 0


# ---------- Real WALS checks -------------------------------------------------


def test_wals_marginal_austronesian_svo(wals):
    m = Marginal(
        wals,
        "81A",
        condition={"Family": "Austronesian"},
        estimator=estimators.laplace(0.5),
    )
    dist = m.distribution
    # Austronesian is overwhelmingly VSO/VOS/SVO, not SOV
    p = dist.probabilities
    # SOV = 81A-1, SVO = 81A-2, VSO = 81A-3, VOS = 81A-4
    assert p.get("81A-2", 0) + p.get("81A-3", 0) + p.get("81A-4", 0) > p.get("81A-1", 0)
    assert dist.n_observations > 30  # plenty of Austronesian langs have 81A


def test_wals_conditional_word_order_informative(wals):
    # Object-Verb order (83A) is strongly correlated with SV/OV order (81A).
    cpt = Conditional(
        wals, target="83A", given="81A", estimator=estimators.laplace(0.5)
    )
    # MI should be clearly positive (these features are highly correlated)
    mi = cpt.mutual_information()
    assert mi > 0.3  # bits, generous lower bound
