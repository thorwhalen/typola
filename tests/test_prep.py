"""Tests for the data-prep layer (CLDF → Typology → counts)."""

from __future__ import annotations

import pandas as pd

from typola import Typology


def test_toy_typology_repr(toy_typology):
    r = repr(toy_typology)
    assert "n_languages=4" in r
    assert "n_parameters=2" in r


def test_toy_counts(toy_typology):
    # SV_order: 3 languages have SV (P1-1), 1 has VS (P1-2)
    c = toy_typology.counts("SV_order")
    assert c.loc["P1-1"] == 3
    assert c.loc["P1-2"] == 1
    assert c.sum() == 4


def test_toy_counts_by_name(toy_typology):
    # name-based lookup works
    c = toy_typology.counts("SV_order")
    assert c.sum() == 4


def test_toy_counts_conditioned(toy_typology):
    # Under Family==F1: both languages have SV
    c = toy_typology.counts("SV_order", condition={"Family": "F1"})
    assert c.loc["P1-1"] == 2
    assert c.loc["P1-2"] == 0


def test_toy_joint_counts(toy_typology):
    jc = toy_typology.joint_counts("SV_order", "Tone")
    # SV (P1-1) with Tone values:
    #   a: P2-2 (simple),  b: P2-3 (complex),  d: P2-1 (none)
    assert jc.loc["P1-1", "P2-1"] == 1
    assert jc.loc["P1-1", "P2-2"] == 1
    assert jc.loc["P1-1", "P2-3"] == 1
    # VS (P1-2):  c: P2-1 (none)
    assert jc.loc["P1-2", "P2-1"] == 1
    assert jc.values.sum() == 4


def test_counts_include_unobserved_codes(toy_typology):
    # Even when a code is never observed, it should appear with count 0
    # under F1 condition, VS is unobserved.
    c = toy_typology.counts("SV_order", condition={"Family": "F1"})
    assert "P1-2" in c.index
    assert c.loc["P1-2"] == 0


# ---------------------------------------------------------------------------
# real WALS smoke test (skipped if local copy absent)
# ---------------------------------------------------------------------------


def test_load_real_wals(wals):
    # shape matches what the original project reported
    assert len(wals.parameters) > 150
    assert len(wals.languages) > 2000
    # the iconic SV-order parameter is 81A
    assert "81A" in wals.parameters.index
    row = wals.parameters.loc["81A"]
    assert "Subject" in row["Name"] or "SV" in row["Name"]


def test_wals_counts_81A(wals):
    # Globally: SVO (81A-2) should be common; OVS (81A-5) should be rare.
    c = wals.counts("81A")
    # each code appears at least once in the catalog, counts are non-negative
    assert (c >= 0).all()
    # Some languages should have been counted
    assert c.sum() > 100
    # SVO (81A-2) and SOV (81A-1) are the most common globally
    top2 = c.sort_values(ascending=False).head(2).index.tolist()
    assert set(top2) == {"81A-1", "81A-2"}


def test_wals_counts_conditioned_by_family(wals):
    # Austronesian languages: mostly VSO, VOS, or SVO, very few SOV
    c_austro = wals.counts("81A", condition={"Family": "Austronesian"})
    c_global = wals.counts("81A")
    # Family-conditioned sum ≤ global sum
    assert c_austro.sum() <= c_global.sum()
    # And ≥ 1 observation
    assert c_austro.sum() > 0
