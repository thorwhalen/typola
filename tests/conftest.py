"""Pytest fixtures. Provides a real WALS typology for tests when available,
falling back to a tiny synthetic typology otherwise.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from typola import load_from_cldf_dir, Typology


# Local WALS copy bundled with the user's dig4el project — used so tests can
# run without network. Override with TYPOLA_WALS_LOCAL.
_DEFAULT_WALS = Path(
    "/Users/thorwhalen/Dropbox/py/proj/etc/dig4el/external_data/wals-master"
)
_DEFAULT_GB = Path(
    "/Users/thorwhalen/Dropbox/py/proj/etc/dig4el/external_data/grambank-1.0.3"
)


@pytest.fixture(scope="session")
def wals_local_path() -> Path | None:
    p = Path(os.environ.get("TYPOLA_WALS_LOCAL", str(_DEFAULT_WALS)))
    return p if p.exists() else None


@pytest.fixture(scope="session")
def grambank_local_path() -> Path | None:
    p = Path(os.environ.get("TYPOLA_GRAMBANK_LOCAL", str(_DEFAULT_GB)))
    return p if p.exists() else None


@pytest.fixture(scope="session")
def wals(wals_local_path) -> Typology:
    if wals_local_path is None:
        pytest.skip("No local WALS copy available for tests")
    return load_from_cldf_dir(wals_local_path, name="wals")


@pytest.fixture(scope="session")
def grambank(grambank_local_path) -> Typology:
    if grambank_local_path is None:
        pytest.skip("No local Grambank copy available for tests")
    return load_from_cldf_dir(grambank_local_path, name="grambank")


@pytest.fixture()
def toy_typology() -> Typology:
    """A tiny 3-language, 2-parameter typology used for fast unit tests."""
    languages = pd.DataFrame(
        [
            {"Name": "Lang A", "Family": "F1", "Macroarea": "Africa"},
            {"Name": "Lang B", "Family": "F1", "Macroarea": "Africa"},
            {"Name": "Lang C", "Family": "F2", "Macroarea": "Eurasia"},
            {"Name": "Lang D", "Family": "F2", "Macroarea": "Eurasia"},
        ],
        index=pd.Index(["a", "b", "c", "d"], name="ID"),
    )
    parameters = pd.DataFrame(
        [{"Name": "SV_order", "Description": ""}, {"Name": "Tone", "Description": ""}],
        index=pd.Index(["P1", "P2"], name="ID"),
    )
    codes = pd.DataFrame(
        [
            {"Parameter_ID": "P1", "Name": "SV", "Number": 1},
            {"Parameter_ID": "P1", "Name": "VS", "Number": 2},
            {"Parameter_ID": "P2", "Name": "none", "Number": 1},
            {"Parameter_ID": "P2", "Name": "simple", "Number": 2},
            {"Parameter_ID": "P2", "Name": "complex", "Number": 3},
        ],
        index=pd.Index(["P1-1", "P1-2", "P2-1", "P2-2", "P2-3"], name="ID"),
    )
    values = pd.DataFrame(
        [
            {"Language_ID": "a", "Parameter_ID": "P1", "Value": 1, "Code_ID": "P1-1"},
            {"Language_ID": "b", "Parameter_ID": "P1", "Value": 1, "Code_ID": "P1-1"},
            {"Language_ID": "c", "Parameter_ID": "P1", "Value": 2, "Code_ID": "P1-2"},
            {"Language_ID": "d", "Parameter_ID": "P1", "Value": 1, "Code_ID": "P1-1"},
            {"Language_ID": "a", "Parameter_ID": "P2", "Value": 2, "Code_ID": "P2-2"},
            {"Language_ID": "b", "Parameter_ID": "P2", "Value": 3, "Code_ID": "P2-3"},
            {"Language_ID": "c", "Parameter_ID": "P2", "Value": 1, "Code_ID": "P2-1"},
            {"Language_ID": "d", "Parameter_ID": "P2", "Value": 1, "Code_ID": "P2-1"},
        ]
    )
    return Typology(
        name="toy",
        languages=languages,
        parameters=parameters,
        codes=codes,
        values=values,
    )
