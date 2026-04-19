"""Tests for conditioning on another parameter's value (drill-down)."""
from __future__ import annotations

import numpy as np

from semix import estimators, query


def test_parameter_condition_filters_toy(toy_typology):
    # Condition: Tone = P2-1 (none). Languages c, d.
    # Both have SV_order = P1-2 (c) and P1-1 (d) → 1 each.
    s = toy_typology.counts(
        "SV_order", parameter_conditions={"Tone": "P2-1"}
    )
    assert s.loc["P1-1"] == 1  # lang d
    assert s.loc["P1-2"] == 1  # lang c
    assert s.sum() == 2


def test_parameter_condition_combines_with_language_condition(toy_typology):
    # Tone=P2-1 AND Family=F2 → only lang c (SV_order=P1-2), lang d (SV_order=P1-1)
    s = toy_typology.counts(
        "SV_order",
        condition={"Family": "F2"},
        parameter_conditions={"Tone": "P2-1"},
    )
    assert s.sum() == 2


def test_parameter_condition_iterable(toy_typology):
    # Tone in {P2-2, P2-3} → langs a, b (both have SV_order=P1-1)
    s = toy_typology.counts(
        "SV_order", parameter_conditions={"Tone": ["P2-2", "P2-3"]}
    )
    assert s.loc["P1-1"] == 2
    assert s.loc["P1-2"] == 0


def test_query_drilldown_on_parameter_condition(toy_typology):
    # P(SV_order | Tone = P2-1), Jeffreys
    d = query(
        toy_typology, target="SV_order",
        parameter_conditions={"Tone": "P2-1"},
        estimator=estimators.jeffreys(),
    )
    # counts are 1,1 → symmetric with Jeffreys → probs ~ 0.5, 0.5
    assert np.isclose(d.probabilities["P1-1"], 0.5)
    assert np.isclose(d.probabilities["P1-2"], 0.5)


# --- real WALS ----------------------------------------------------------

def test_wals_drilldown_by_verb_object_order(wals):
    # P(81A | 83A = OV) — strongly biased toward SOV
    d = query(
        wals, target="81A",
        parameter_conditions={"83A": "83A-1"},  # Object-Verb (OV)
        estimator=estimators.laplace(0.5),
    )
    assert d.mode() == "81A-1"  # SOV is the mode when OV
    # SOV should dominate
    assert d.probabilities["81A-1"] > 0.5


def test_wals_drilldown_compound(wals):
    # P(81A | 83A = OV AND Family = Indo-European)
    d = query(
        wals, target="81A",
        condition={"Family": "Indo-European"},
        parameter_conditions={"83A": "83A-1"},
        estimator=estimators.laplace(0.5),
    )
    # Indo-European OV-languages are overwhelmingly SOV
    assert d.mode() == "81A-1"
