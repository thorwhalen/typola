"""High-level query and drill-down API.

The `query` function is the everyday entry point. Pass a typology, a target
parameter, and optionally a conditioning parameter or language filter. Get
back a distribution or a full conditional probability table.

Beyond individual queries, this module provides a small comparison layer so
you can (a) try several estimators on the same question and (b) rank
parameters by how informative they are about a target.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Union

import pandas as pd

from typola.estimators import Estimator, jeffreys, held_out_score
from typola.models.conditional import Conditional
from typola.models.distribution import Distribution
from typola.models.marginal import Marginal
from typola.prep.canonical import Typology


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------


def query(
    typology: Typology,
    target: str,
    *,
    given: Optional[str] = None,
    given_value: Optional[Any] = None,
    condition: Optional[Mapping[str, Any]] = None,
    parameter_conditions: Optional[Mapping[str, Any]] = None,
    estimator: Optional[Estimator] = None,
    drop_missing: bool = True,
) -> Union[Distribution, Conditional]:
    """Ask a probabilistic question about the typology.

    Parameters
    ----------
    typology : Typology
    target : str
        Parameter ID or name to ask about.
    given : str, optional
        Parameter ID or name to condition on. If given without ``given_value``,
        the full CPT is returned. With ``given_value``, the row distribution
        is returned.
    given_value : any, optional
        A specific code/value of the ``given`` parameter.
    condition : mapping, optional
        Filter on language metadata (see `Typology.filter_languages`).
    estimator : Estimator, optional
        Count-to-probability strategy. Defaults to Jeffreys.

    Returns
    -------
    Distribution
        When ``given`` is None, or ``given`` and ``given_value`` are both set.
    Conditional
        When ``given`` is a parameter and ``given_value`` is omitted.
    """
    estimator = estimator or jeffreys()

    if given is None:
        return Marginal(
            typology, target,
            condition=condition,
            parameter_conditions=parameter_conditions,
            estimator=estimator,
            drop_missing=drop_missing,
        ).distribution

    cpt = Conditional(
        typology, target=target, given=given,
        condition=condition,
        parameter_conditions=parameter_conditions,
        estimator=estimator,
        drop_missing=drop_missing,
    )
    if given_value is None:
        return cpt
    return cpt.p_given(given_value)


# ---------------------------------------------------------------------------
# compare estimators on the same question
# ---------------------------------------------------------------------------


def compare_estimators(
    typology: Typology,
    target: str,
    estimators: Iterable[Estimator],
    *,
    condition: Optional[Mapping[str, Any]] = None,
) -> pd.DataFrame:
    """Return a side-by-side DataFrame of P(value) under each estimator.

    Columns are estimator names; rows are codes (with a ``name`` column).
    Useful as a first-line sanity check when picking a smoothing strategy.
    """
    estimators = list(estimators)
    if not estimators:
        raise ValueError("compare_estimators requires at least one estimator")
    labels = _unique_labels(estimators)
    # Reference distribution for labels & counts
    first = Marginal(typology, target, condition=condition, estimator=estimators[0]).distribution
    frame = first.to_frame().copy()
    frame = frame.rename(columns={"probability": labels[0]})
    for est, lbl in zip(estimators[1:], labels[1:]):
        d = Marginal(typology, target, condition=condition, estimator=est).distribution
        frame[lbl] = d.probabilities.reindex(frame.index)
    return frame


def _unique_labels(estimators: list) -> list[str]:
    """Return display labels for a list of estimators, using repr() when names collide."""
    names = [e.name for e in estimators]
    if len(set(names)) == len(names):
        return names
    return [repr(e) for e in estimators]


def cross_validate_estimators(
    typology: Typology,
    target: str,
    estimators: Iterable[Estimator],
    *,
    n_folds: int = 5,
    condition: Optional[Mapping[str, Any]] = None,
    random_state: Optional[int] = None,
) -> pd.DataFrame:
    """Cross-validated comparison: average held-out log-likelihood per fold.

    Splits observed language IDs for ``target`` into ``n_folds``, holds each
    fold out, fits each estimator on the rest, and scores on the fold.
    """
    import numpy as np

    estimators = list(estimators)
    pid = typology.parameter_id(target)
    vals = typology.values[typology.values["Parameter_ID"] == pid]
    if condition:
        keep = typology.filter_languages(condition)
        vals = vals[vals["Language_ID"].isin(keep)]
    vals = vals.dropna(subset=["Code_ID"] if "Code_ID" in vals.columns else ["Value"])
    use_code = "Code_ID" in vals.columns and vals["Code_ID"].notna().any()
    col = "Code_ID" if use_code else "Value"
    lang_code_pairs = list(zip(vals["Language_ID"].tolist(), vals[col].tolist()))

    rng = np.random.default_rng(random_state)
    order = np.arange(len(lang_code_pairs))
    rng.shuffle(order)
    folds = np.array_split(order, n_folds)
    codes_index = typology.codes.index[typology.codes["Parameter_ID"] == pid]

    def _counts(pairs) -> pd.Series:
        s = pd.Series([c for _, c in pairs]).value_counts()
        return s.reindex(codes_index, fill_value=0).astype(int)

    rows = []
    for i, test_idx in enumerate(folds):
        test_pairs = [lang_code_pairs[j] for j in test_idx]
        train_pairs = [lang_code_pairs[j] for j in order if j not in set(test_idx.tolist())]
        c_train = _counts(train_pairs).to_numpy()
        c_test = _counts(test_pairs).to_numpy()
        for est in estimators:
            score = held_out_score(est, c_train, c_test)
            score["fold"] = i
            score["name"] = repr(est)  # include params so distinct configs don't collapse
            rows.append(score)
    df = pd.DataFrame(rows)
    return (
        df.groupby("name")[["log_likelihood", "perplexity", "kl_to_empirical"]]
        .mean()
        .sort_values("log_likelihood", ascending=False)
    )


# ---------------------------------------------------------------------------
# rank associations: which parameters are most informative about target?
# ---------------------------------------------------------------------------


def rank_associations(
    typology: Typology,
    target: str,
    *,
    top_k: int = 20,
    estimator: Optional[Estimator] = None,
    min_observations: int = 30,
    condition: Optional[Mapping[str, Any]] = None,
) -> pd.DataFrame:
    """For each other parameter X, compute MI(X; target) and rank.

    Useful for "what is most predictive of target parameter Y?". Slow for
    large typologies (O(n_parameters)); consider restricting the parameter
    set via ``typology.parameters`` pre-filtering in practice.
    """
    estimator = estimator or jeffreys()
    target_id = typology.parameter_id(target)
    rows = []
    for pid in typology.parameters.index:
        if pid == target_id:
            continue
        try:
            cpt = Conditional(
                typology, target=target_id, given=pid,
                condition=condition, estimator=estimator,
            )
        except Exception:
            continue
        n = int(cpt.joint_counts.to_numpy().sum())
        if n < min_observations:
            continue
        rows.append(
            {
                "parameter_id": pid,
                "parameter_name": str(typology.parameters.loc[pid].get("Name", "")),
                "mutual_information": cpt.mutual_information(),
                "n_languages": n,
            }
        )
    df = pd.DataFrame(rows)
    return df.sort_values("mutual_information", ascending=False).head(top_k).reset_index(drop=True)


# ---------------------------------------------------------------------------
# compare conditions: how does P(target) change across condition groups?
# ---------------------------------------------------------------------------


def compare_conditions(
    typology: Typology,
    target: str,
    conditions: Mapping[str, Mapping[str, Any]],
    *,
    estimator: Optional[Estimator] = None,
) -> pd.DataFrame:
    """Show P(target) under each of several named conditions.

    ``conditions`` maps a label → a condition dict. Returns a wide DataFrame:
    rows are codes; one column per condition label, plus ``name`` and a global
    unconditioned baseline.
    """
    estimator = estimator or jeffreys()
    # global baseline
    base = Marginal(typology, target, estimator=estimator).distribution
    frame = base.to_frame().copy().rename(columns={"probability": "overall"}).drop(columns="count")
    for label, cond in conditions.items():
        d = Marginal(typology, target, condition=cond, estimator=estimator).distribution
        frame[label] = d.probabilities.reindex(frame.index)
    return frame
