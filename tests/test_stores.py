"""Tests for dol-style stores."""

from __future__ import annotations

import pandas as pd

from typola.prep import CountsStore, TypologyStore


def test_typology_store_lists_registered_sources():
    ts = TypologyStore()
    assert "wals" in ts
    assert "grambank" in ts
    assert len(ts) >= 2


def test_typology_store_loads_from_local_path(wals_local_path, grambank_local_path):
    if wals_local_path is None:
        return
    paths = {"wals": str(wals_local_path)}
    if grambank_local_path is not None:
        paths["grambank"] = str(grambank_local_path)
    ts = TypologyStore(local_paths=paths)
    tp = ts["wals"]
    assert tp.name == "wals"
    # second access should come from cache (same object)
    assert ts["wals"] is tp


def test_counts_store_iterates_parameters(toy_typology):
    cs = CountsStore(toy_typology)
    assert len(cs) == 2
    params = sorted(cs)
    assert params == ["P1", "P2"]
    s = cs["P1"]
    assert isinstance(s, pd.Series)
    assert s.sum() == 4  # 4 languages observed for SV_order


def test_counts_store_with_condition(toy_typology):
    cs = CountsStore(toy_typology, condition={"Family": "F1"})
    s = cs["P1"]
    assert s.loc["P1-1"] == 2
    assert s.loc["P1-2"] == 0
