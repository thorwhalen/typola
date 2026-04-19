"""Bake-off example: comparing estimation strategies on real WALS data.

Runs:
  1. Shows the global marginal for parameter 81A (Order of Subject and Verb).
  2. Compares several estimators on the Austronesian subset.
  3. Cross-validates those estimators and reports held-out log-likelihood.
  4. Shows the top parameters most informative about 81A globally.

Run with:
    python misc/example_bakeoff.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from semix import estimators, load_from_cldf_dir, query
from semix.query import (
    compare_conditions,
    compare_estimators,
    cross_validate_estimators,
    rank_associations,
)

# Use local WALS copy (from the dig4el project) for reproducibility.
# Falls back to download if not present.
LOCAL_WALS = Path("/Users/thorwhalen/Dropbox/py/proj/etc/dig4el/external_data/wals-master")


def _section(title: str) -> None:
    print(f"\n\n{'=' * 72}\n {title}\n{'=' * 72}")


def main() -> None:
    pd.options.display.max_colwidth = 60

    if LOCAL_WALS.exists():
        wals = load_from_cldf_dir(LOCAL_WALS, name="wals")
    else:
        from semix import load
        wals = load("wals")
    print(wals)

    # ---- 1. Global marginal -----------------------------------------------
    _section("Global P(81A = Order of Subject and Verb), Jeffreys")
    d = query(wals, target="81A", estimator=estimators.jeffreys())
    print(d.to_frame().to_string())
    print(f"\nEntropy: {d.entropy():.3f} bits  (normalized: {d.normalized_entropy():.3f})")
    print(f"Mode:    {d.mode()}  ({d.support_labels[d.mode()]})")

    # ---- 2. Estimator comparison on a small subset ------------------------
    _section("P(81A | Austronesian) under several estimators")
    global_counts = wals.counts("81A").values
    frame = compare_estimators(
        wals, target="81A",
        condition={"Family": "Austronesian"},
        estimators=[
            estimators.mle(),
            estimators.laplace(1.0),
            estimators.jeffreys(),
            estimators.dirichlet("jeffreys"),
            estimators.empirical_bayes(global_counts, strength=5.0),
            estimators.empirical_bayes(global_counts, strength=50.0),
        ],
    )
    print(frame.to_string(float_format=lambda x: f"{x:.4f}"))

    # ---- 3. Cross-validated comparison ------------------------------------
    _section("5-fold CV log-likelihood (Austronesian subset, higher = better)")
    df = cross_validate_estimators(
        wals, target="81A",
        estimators=[
            estimators.mle(),
            estimators.laplace(0.1),
            estimators.laplace(0.5),
            estimators.laplace(1.0),
            estimators.empirical_bayes(global_counts, strength=5.0),
            estimators.empirical_bayes(global_counts, strength=50.0),
        ],
        n_folds=5,
        random_state=42,
        condition={"Family": "Austronesian"},
    )
    print(df.round(4).to_string())

    # ---- 4. What varies most across families? -----------------------------
    _section("P(81A) across language families")
    frame = compare_conditions(
        wals, target="81A",
        conditions={
            "Austronesian": {"Family": "Austronesian"},
            "Indo-European": {"Family": "Indo-European"},
            "Afro-Asiatic": {"Family": "Afro-Asiatic"},
            "Niger-Congo": {"Family": "Niger-Congo"},
            "Sino-Tibetan": {"Family": "Sino-Tibetan"},
        },
        estimator=estimators.laplace(0.5),
    )
    print(frame.to_string(float_format=lambda x: f"{x:.3f}"))

    # ---- 5. Top parameters informative about 81A --------------------------
    _section("Top 8 parameters most informative about 81A (MI)")
    df = rank_associations(wals, target="81A", top_k=8, estimator=estimators.laplace(0.5))
    print(df.round(3).to_string())

    # ---- 6. Drill down: combine language and parameter conditions ----------
    _section("Drill: P(81A) in several slices")
    cases = [
        ("Globally, no condition", {}, {}),
        ("Object-Verb order (83A=OV)", {}, {"83A": "83A-1"}),
        ("Indo-European AND OV", {"Family": "Indo-European"}, {"83A": "83A-1"}),
        ("Niger-Congo AND VO", {"Family": "Niger-Congo"}, {"83A": "83A-2"}),
        ("Austronesian AND VO", {"Family": "Austronesian"}, {"83A": "83A-2"}),
    ]
    for label, cond, pcond in cases:
        d = query(
            wals, target="81A",
            condition=cond or None,
            parameter_conditions=pcond or None,
            estimator=estimators.laplace(0.5),
        )
        top = d.top_k(1).iloc[0]
        print(
            f"  {label:<40s}  n={d.n_observations:4d}  "
            f"mode={top['name']:<18s} p={top['probability']:.3f}  "
            f"H={d.entropy():.2f} bits"
        )


if __name__ == "__main__":
    main()
