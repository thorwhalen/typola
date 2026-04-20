"""Tests for the FastAPI app in webapp.api.main."""
from __future__ import annotations

import os

import pytest

fastapi = pytest.importorskip("fastapi")


@pytest.fixture()
def client(wals_local_path):
    if wals_local_path is None:
        pytest.skip("No local WALS copy available")
    os.environ["SEMIX_TYPOLOGY_WALS_PATH"] = str(wals_local_path)
    from fastapi.testclient import TestClient
    from webapp.api.main import app
    return TestClient(app)


def test_list_typologies(client):
    r = client.get("/api/typologies")
    assert r.status_code == 200
    items = r.json()
    assert any(it["name"] == "wals" for it in items)


def test_list_parameters(client):
    r = client.get("/api/typologies/wals/parameters")
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 150
    assert any(p["id"] == "81A" for p in items)


def test_list_codes_81a(client):
    r = client.get("/api/typologies/wals/parameters/81A/codes")
    assert r.status_code == 200
    codes = r.json()
    code_names = {c["name"] for c in codes}
    assert {"SOV", "SVO", "VSO"}.issubset(code_names)


def test_list_language_columns(client):
    r = client.get("/api/typologies/wals/languages/columns")
    cols = {c["name"] for c in r.json()}
    assert {"Family", "Macroarea", "Genus"}.issubset(cols)


def test_query_marginal(client):
    r = client.post(
        "/api/query",
        json={"typology": "wals", "target": "81A", "estimator": {"name": "jeffreys"}},
    )
    assert r.status_code == 200
    j = r.json()
    assert j["kind"] == "distribution"
    assert j["mode_name"] == "SOV"
    assert j["support"][0]["name"] == "SOV"


def test_query_parameter_condition(client):
    r = client.post(
        "/api/query",
        json={
            "typology": "wals",
            "target": "81A",
            "parameter_conditions": {"83A": "83A-1"},
            "estimator": {"name": "laplace", "params": {"alpha": 0.5}},
        },
    )
    assert r.status_code == 200
    j = r.json()
    assert j["mode_name"] == "SOV"
    assert j["n_observations"] > 500


def test_query_cpt(client):
    r = client.post(
        "/api/query",
        json={
            "typology": "wals",
            "target": "83A",
            "given": "81A",
            "estimator": {"name": "laplace", "params": {"alpha": 0.5}},
        },
    )
    assert r.status_code == 200
    j = r.json()
    assert j["kind"] == "conditional"
    assert j["mutual_information_bits"] > 1.0
    assert len(j["rows"]) == 7  # 81A has 7 codes
    # Each row sums to ~1
    for probs in j["cell_probabilities"]:
        assert abs(sum(probs) - 1.0) < 1e-6


def test_rank_associations(client):
    r = client.post(
        "/api/rank-associations",
        json={"typology": "wals", "target": "81A", "top_k": 5},
    )
    assert r.status_code == 200
    j = r.json()
    top_ids = [row["parameter_id"] for row in j["rows"]]
    assert "83A" in top_ids


def test_compare_estimators(client):
    r = client.post(
        "/api/compare-estimators",
        json={
            "typology": "wals",
            "target": "81A",
            "condition": {"Family": "Austronesian"},
            "estimators": [
                {"name": "mle"},
                {"name": "jeffreys"},
                {"name": "laplace", "params": {"alpha": 1.0}},
            ],
        },
    )
    assert r.status_code == 200
    j = r.json()
    assert j["estimator_labels"] == ["mle", "jeffreys", "laplace(alpha=1.0)"]
    # Each row has a probability per estimator
    for row in j["rows"]:
        assert set(row["probabilities"]) == set(j["estimator_labels"])
