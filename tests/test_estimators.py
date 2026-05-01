"""Tests for count-to-probability estimators."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from typola import estimators


# ---------------------------------------------------------------------------
# basic invariants each estimator must satisfy
# ---------------------------------------------------------------------------

ESTIMATORS_FOR_NONZERO = [
    estimators.mle(),
    estimators.laplace(0.5),
    estimators.laplace(1.0),
    estimators.jeffreys(),
    estimators.dirichlet("jeffreys"),
    estimators.dirichlet("uniform"),
    estimators.dirichlet(2.0),
    estimators.empirical_bayes([10, 5, 85], strength=1.0),
    estimators.uniform(),
    estimators.mix((0.5, estimators.laplace(1)), (0.5, estimators.mle())),
]


@pytest.mark.parametrize("est", ESTIMATORS_FOR_NONZERO, ids=lambda e: e.name)
def test_output_sums_to_one(est):
    counts = np.array([3, 1, 6])
    probs = est(counts)
    assert abs(probs.sum() - 1.0) < 1e-12


@pytest.mark.parametrize("est", ESTIMATORS_FOR_NONZERO, ids=lambda e: e.name)
def test_output_non_negative(est):
    counts = np.array([3, 1, 6])
    probs = est(counts)
    assert (probs >= -1e-12).all()


@pytest.mark.parametrize("est", ESTIMATORS_FOR_NONZERO, ids=lambda e: e.name)
def test_output_preserves_index_for_series(est):
    s = pd.Series([3, 1, 6], index=["SV", "VS", "OVS"])
    p = est(s)
    assert isinstance(p, pd.Series)
    assert list(p.index) == ["SV", "VS", "OVS"]


# ---------------------------------------------------------------------------
# specific numeric behaviors
# ---------------------------------------------------------------------------


def test_mle_matches_proportions():
    counts = np.array([2, 3, 5])
    probs = estimators.mle()(counts)
    assert np.allclose(probs, [0.2, 0.3, 0.5])


def test_mle_fails_on_all_zero():
    with pytest.raises(ValueError):
        estimators.mle()(np.zeros(3))


def test_laplace_adds_alpha_per_category():
    counts = np.array([0, 0, 10])
    probs = estimators.laplace(1.0)(counts)
    # (0+1)/(0+0+10 + 3*1) = 1/13 for the zero cells, 11/13 for the observed
    assert np.isclose(probs[0], 1 / 13)
    assert np.isclose(probs[2], 11 / 13)


def test_jeffreys_equals_laplace_half():
    c = np.array([2, 0, 3])
    p_j = estimators.jeffreys()(c)
    p_l = estimators.laplace(0.5)(c)
    assert np.allclose(p_j, p_l)


def test_dirichlet_jeffreys_matches_laplace_half():
    c = np.array([5, 0, 2, 3])
    assert np.allclose(estimators.dirichlet("jeffreys")(c), estimators.jeffreys()(c))


def test_dirichlet_uniform_matches_laplace_one():
    c = np.array([5, 0, 2, 3])
    assert np.allclose(estimators.dirichlet("uniform")(c), estimators.laplace(1.0)(c))


def test_dirichlet_scalar_prior():
    c = np.array([1, 2, 3])
    # prior=0 → MLE
    assert np.allclose(estimators.dirichlet(0.0)(c), estimators.mle()(c))


def test_dirichlet_vector_prior():
    c = np.array([0, 0, 10])
    # heavy asymmetric prior on first category
    p = estimators.dirichlet([10, 0.1, 0.1])(c)
    assert p[0] > p[1]  # prior dominates in the near-zero cell


def test_dirichlet_handles_all_zero_counts():
    c = np.zeros(3)
    p = estimators.dirichlet("jeffreys")(c)
    assert np.allclose(p, 1 / 3)


def test_empirical_bayes_shrinks_toward_global():
    global_counts = np.array([100, 10, 10])  # global skewed to category 0
    local = np.array([1, 5, 4])  # local prefers category 1
    # Heavy shrinkage should pull category 0 probability up
    p_mle = estimators.mle()(local)
    p_eb = estimators.empirical_bayes(global_counts, strength=100)(local)
    assert p_eb[0] > p_mle[0]  # moved toward the global
    assert p_eb[1] < p_mle[1]


def test_empirical_bayes_zero_strength_reduces_to_mle():
    global_counts = np.array([100, 10, 10])
    local = np.array([1, 5, 4])
    p_eb = estimators.empirical_bayes(global_counts, strength=0.0)(local)
    p_mle = estimators.mle()(local)
    assert np.allclose(p_eb, p_mle)


def test_uniform_ignores_counts():
    for c in ([1, 2, 3, 4], [10, 0, 0, 0], [0, 0, 0, 0]):
        p = estimators.uniform()(np.array(c))
        assert np.allclose(p, 0.25)


def test_mixture_is_convex_combination():
    c = np.array([1, 2, 3])
    p_a = estimators.laplace(1)(c)
    p_b = estimators.mle()(c)
    p_mix = estimators.mix((0.5, estimators.laplace(1)), (0.5, estimators.mle()))(c)
    assert np.allclose(p_mix, 0.5 * p_a + 0.5 * p_b)


def test_estimator_describe_is_self_documenting():
    est = estimators.laplace(0.5)
    d = est.describe()
    assert d["name"] == "laplace"
    assert d["alpha"] == 0.5


# ---------------------------------------------------------------------------
# evaluation / comparison harness
# ---------------------------------------------------------------------------


def test_held_out_score_prefers_laplace_over_mle_when_unseen_categories():
    # Train has 0 counts in one category; test has some → MLE will log(0) = -inf,
    # while Laplace gives a finite score.
    train = np.array([8, 2, 0])
    test = np.array([2, 1, 1])  # the "unseen" category shows up in test

    eval_mle = estimators.held_out_score(estimators.mle(), train, test)
    eval_laplace = estimators.held_out_score(estimators.laplace(1.0), train, test)

    # Laplace finite, MLE very negative (because test mass on a zero-probability cell)
    assert eval_laplace["log_likelihood"] > eval_mle["log_likelihood"]


def test_held_out_score_has_expected_keys():
    train = np.array([5, 3, 2])
    test = np.array([4, 2, 4])
    res = estimators.held_out_score(estimators.jeffreys(), train, test)
    assert "log_likelihood" in res
    assert "perplexity" in res
    assert "kl_to_empirical" in res
    assert res["name"] == "jeffreys"
