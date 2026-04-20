"""FastAPI app for semix.

Run with::

    uvicorn webapp.api.main:app --reload --port 8765

Or from a script::

    python -m webapp.api.main
"""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from semix import estimators as est_factory
from semix import query as semix_query
from semix.query import (
    compare_estimators,
    cross_validate_estimators,
    rank_associations,
)
from semix.sources.base import list_sources

from webapp.api.deps import build_estimator, get_typology
from webapp.api.schemas import (
    AssociationRow,
    CodeSummary,
    CompareEstimatorsRequest,
    CompareEstimatorsResult,
    CompareEstimatorsRow,
    ConditionalResult,
    CrossValidateRequest,
    CrossValidateResult,
    CrossValidateRow,
    DistributionResult,
    EstimatorSpec,
    LanguageColumn,
    ParameterSummary,
    QueryRequest,
    QueryResult,
    RankAssociationsRequest,
    RankAssociationsResult,
    SupportItem,
    TypologySummary,
)


app = FastAPI(title="semix", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _resolve_estimator(spec: EstimatorSpec, typology_name: str, target: str):
    """Turn a serializable EstimatorSpec into a live Estimator.

    Handles the empirical_bayes special case (needs global counts from server).
    """
    if spec.name == "empirical_bayes":
        tp = get_typology(typology_name)
        global_counts = tp.counts(target).to_numpy()
        strength = spec.params.get("strength", 1.0)
        return est_factory.empirical_bayes(global_counts, strength=strength)
    return build_estimator(spec)


def _estimator_label(spec: EstimatorSpec) -> str:
    if not spec.params:
        return spec.name
    parts = ", ".join(f"{k}={v}" for k, v in spec.params.items())
    return f"{spec.name}({parts})"


def _code_summaries_for(tp, pid: str) -> list[CodeSummary]:
    sub = tp.codes[tp.codes["Parameter_ID"] == pid]
    return [
        CodeSummary(
            id=idx,
            parameter_id=pid,
            name=str(row.get("Name", "")),
            description=str(row.get("Description", "") or ""),
        )
        for idx, row in sub.iterrows()
    ]


# ---------------------------------------------------------------------------
# metadata endpoints
# ---------------------------------------------------------------------------


@app.get("/api/typologies")
def list_typologies() -> list[TypologySummary]:
    out = []
    for name in list_sources():
        try:
            tp = get_typology(name)
        except Exception:
            # source not yet cached and download failed; skip silently
            continue
        from semix.sources.base import get_source

        spec = get_source(name)
        out.append(
            TypologySummary(
                name=name,
                n_languages=len(tp.languages),
                n_parameters=len(tp.parameters),
                n_codes=len(tp.codes),
                n_values=len(tp.values),
                citation=tp.citation or spec.citation,
                license=spec.license,
            )
        )
    return out


@app.get("/api/typologies/{name}/parameters")
def list_parameters(name: str) -> list[ParameterSummary]:
    tp = get_typology(name)
    params = tp.parameters
    n_codes_by_pid = tp.codes["Parameter_ID"].value_counts().to_dict()
    out = []
    for pid, row in params.iterrows():
        out.append(
            ParameterSummary(
                id=pid,
                name=str(row.get("Name", "")),
                description=str(row.get("Description", "") or ""),
                n_codes=int(n_codes_by_pid.get(pid, 0)),
            )
        )
    return out


@app.get("/api/typologies/{name}/parameters/{pid}/codes")
def list_codes(name: str, pid: str) -> list[CodeSummary]:
    tp = get_typology(name)
    if pid not in tp.parameters.index:
        raise HTTPException(404, f"Parameter {pid!r} not found in {name!r}")
    return _code_summaries_for(tp, pid)


@app.get("/api/typologies/{name}/languages/columns")
def list_language_columns(name: str) -> list[LanguageColumn]:
    tp = get_typology(name)
    out = []
    # cap dense free-text columns from the UI
    skip = {"Latitude", "Longitude", "Source", "Parent_ID", "ISO639P3code", "GenusIcon", "ISO_codes", "Country_ID"}
    for col in tp.languages.columns:
        if col in skip:
            continue
        series = tp.languages[col]
        nunique = int(series.nunique(dropna=True))
        if nunique == 0 or nunique == len(series):
            continue  # useless as a filter
        samples = (
            series.dropna().astype(str).value_counts().head(8).index.tolist()
        )
        out.append(
            LanguageColumn(
                name=col, dtype=str(series.dtype), n_unique=nunique, sample_values=samples
            )
        )
    # Put the familiar columns first.
    preferred = ["Family", "Genus", "Subfamily", "Macroarea"]
    out.sort(key=lambda c: (c.name not in preferred, c.name))
    return out


@app.get("/api/typologies/{name}/languages/values")
def list_column_values(name: str, column: str, limit: int = 500) -> list[str]:
    tp = get_typology(name)
    if column not in tp.languages.columns:
        raise HTTPException(404, f"Column {column!r} not found")
    vc = tp.languages[column].dropna().astype(str).value_counts().head(limit)
    return vc.index.tolist()


# ---------------------------------------------------------------------------
# core query endpoint
# ---------------------------------------------------------------------------


@app.post("/api/query")
def do_query(req: QueryRequest) -> QueryResult:
    tp = get_typology(req.typology)
    estimator = _resolve_estimator(req.estimator, req.typology, req.target)

    result = semix_query(
        tp,
        target=req.target,
        given=req.given,
        given_value=req.given_value,
        condition=req.condition or None,
        parameter_conditions=req.parameter_conditions or None,
        estimator=estimator,
    )

    # Full CPT case
    if result.__class__.__name__ == "Conditional":
        cpt = result
        rows = _code_summaries_for(tp, cpt.given_id)
        cols = _code_summaries_for(tp, cpt.target_id)
        mat = cpt.as_matrix()
        counts_mat = cpt.joint_counts
        # row order must match the CodeSummary list
        row_ids = [r.id for r in rows]
        col_ids = [c.id for c in cols]
        mat_ordered = mat.reindex(index=row_ids, columns=col_ids).fillna(0.0)
        count_ordered = counts_mat.reindex(index=row_ids, columns=col_ids).fillna(0).astype(int)
        return ConditionalResult(
            target_id=cpt.target_id,
            target_name=str(tp.parameters.loc[cpt.target_id].get("Name", "")),
            given_id=cpt.given_id,
            given_name=str(tp.parameters.loc[cpt.given_id].get("Name", "")),
            typology=req.typology,
            rows=rows,
            cols=cols,
            cell_probabilities=mat_ordered.values.tolist(),
            cell_counts=count_ordered.values.tolist(),
            row_totals=count_ordered.sum(axis=1).tolist(),
            mutual_information_bits=cpt.mutual_information(),
            n_observations=int(count_ordered.values.sum()),
            estimator_name=cpt.estimator.name,
            estimator_params=dict(cpt.estimator.params),
            condition=cpt.condition,
            parameter_conditions=cpt.parameter_conditions,
        )

    # Distribution case (either marginal or a single row of a CPT)
    dist = result
    meta_pid = (
        dist.metadata.get("target_id")
        or dist.metadata.get("parameter_id")
        or req.target
    )
    labels = tp.code_labels(meta_pid)
    support_items = []
    for code_id in dist.probabilities.index:
        nm = str(labels.get(code_id, "")) if labels is not None else str(code_id)
        support_items.append(
            SupportItem(
                id=str(code_id),
                name=nm,
                count=int(dist.counts.get(code_id, 0)),
                probability=float(dist.probabilities.loc[code_id]),
            )
        )

    target_id = meta_pid
    return DistributionResult(
        target_id=str(target_id),
        target_name=str(dist.metadata.get("parameter_name", target_id)),
        typology=req.typology,
        support=support_items,
        n_observations=dist.n_observations,
        entropy_bits=dist.entropy(),
        normalized_entropy=dist.normalized_entropy(),
        mode_id=str(dist.mode()),
        mode_name=str(labels.get(dist.mode(), "")) if labels is not None else str(dist.mode()),
        estimator_name=dist.estimator_name,
        estimator_params=dist.metadata.get("estimator_params", {}),
        condition=dist.metadata.get("condition", {}) or {},
        parameter_conditions=dist.metadata.get("parameter_conditions", {}) or {},
    )


# ---------------------------------------------------------------------------
# compare / cross-validate
# ---------------------------------------------------------------------------


@app.post("/api/compare-estimators")
def do_compare(req: CompareEstimatorsRequest) -> CompareEstimatorsResult:
    tp = get_typology(req.typology)
    ests = [_resolve_estimator(s, req.typology, req.target) for s in req.estimators]
    labels = [_estimator_label(s) for s in req.estimators]

    # Reuse semix.query.compare_estimators but with our own labels (for duplicates).
    frame = compare_estimators(
        tp, target=req.target,
        condition=req.condition or None,
        estimators=ests,
    )
    # The returned frame uses estimator.name; if labels collide, it uses repr()
    # which is verbose. We'll rebuild with our labels.
    # Recompute by running each estimator once; cheaper than you'd think.
    from semix.models.marginal import Marginal

    support_ids: list[str] = []
    base_support_rows: list[SupportItem] = []
    per_label_probs: dict[str, dict[str, float]] = {lbl: {} for lbl in labels}
    pid = tp.parameter_id(req.target)
    code_labels = tp.code_labels(pid)
    counts = tp.counts(
        req.target,
        condition=req.condition or None,
        parameter_conditions=req.parameter_conditions or None,
    )
    for cid, c in counts.items():
        support_ids.append(str(cid))

    for lbl, est in zip(labels, ests):
        m = Marginal(
            tp, req.target,
            condition=req.condition or None,
            parameter_conditions=req.parameter_conditions or None,
            estimator=est,
        ).distribution
        for cid, p in m.probabilities.items():
            per_label_probs[lbl][str(cid)] = float(p)

    rows_out = []
    for cid in support_ids:
        rows_out.append(
            CompareEstimatorsRow(
                id=cid,
                name=str(code_labels.get(cid, "")) if code_labels is not None else cid,
                count=int(counts.get(cid, 0)),
                probabilities={lbl: per_label_probs[lbl].get(cid, 0.0) for lbl in labels},
            )
        )
    return CompareEstimatorsResult(
        target_id=pid,
        target_name=str(tp.parameters.loc[pid].get("Name", "")),
        estimator_labels=labels,
        rows=rows_out,
    )


@app.post("/api/cross-validate")
def do_cv(req: CrossValidateRequest) -> CrossValidateResult:
    tp = get_typology(req.typology)
    ests = [_resolve_estimator(s, req.typology, req.target) for s in req.estimators]
    labels = [_estimator_label(s) for s in req.estimators]

    df = cross_validate_estimators(
        tp, target=req.target,
        estimators=ests,
        n_folds=req.n_folds,
        random_state=req.random_state,
        condition=req.condition or None,
    )
    # df index is repr(estimator); map back to our human labels by best-effort
    # (order of estimators is preserved; use positional mapping)
    rows = []
    for lbl in labels:
        # Find the row whose index starts with the estimator name (best-effort)
        # fallback: positional.
        pass
    # Simplest: re-run cross_validate once per estimator with a single estimator
    # in the list so the index label matches our known label.
    from semix.query.api import cross_validate_estimators as _cv

    rows_out: list[CrossValidateRow] = []
    for lbl, est in zip(labels, ests):
        df1 = _cv(
            tp, target=req.target, estimators=[est],
            n_folds=req.n_folds, random_state=req.random_state,
            condition=req.condition or None,
        )
        r = df1.iloc[0]
        rows_out.append(
            CrossValidateRow(
                label=lbl,
                log_likelihood=float(r["log_likelihood"]),
                perplexity=float(r["perplexity"]),
                kl_to_empirical=float(r["kl_to_empirical"]),
            )
        )
    rows_out.sort(key=lambda r: r.log_likelihood, reverse=True)
    return CrossValidateResult(target_id=tp.parameter_id(req.target), rows=rows_out)


# ---------------------------------------------------------------------------
# rank associations
# ---------------------------------------------------------------------------


@app.post("/api/rank-associations")
def do_rank(req: RankAssociationsRequest) -> RankAssociationsResult:
    tp = get_typology(req.typology)
    est = _resolve_estimator(req.estimator, req.typology, req.target)
    df = rank_associations(
        tp, target=req.target,
        top_k=req.top_k,
        estimator=est,
        min_observations=req.min_observations,
        condition=req.condition or None,
    )
    pid = tp.parameter_id(req.target)
    return RankAssociationsResult(
        target_id=pid,
        target_name=str(tp.parameters.loc[pid].get("Name", "")),
        rows=[
            AssociationRow(
                parameter_id=r["parameter_id"],
                parameter_name=r["parameter_name"],
                mutual_information_bits=float(r["mutual_information"]),
                n_languages=int(r["n_languages"]),
            )
            for _, r in df.iterrows()
        ],
    )


# ---------------------------------------------------------------------------
# script entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8765"))
    uvicorn.run(
        "webapp.api.main:app",
        host="127.0.0.1",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
