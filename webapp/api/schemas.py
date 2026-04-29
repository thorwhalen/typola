"""Pydantic schemas mirroring the types the frontend sees.

Keep these in sync with the zod schemas under webapp/ui/src/lib/schemas.ts.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# metadata
# ---------------------------------------------------------------------------


class TypologySummary(BaseModel):
    name: str
    n_languages: int
    n_parameters: int
    n_codes: int
    n_values: int
    citation: str = ""
    license: str = ""


class ParameterSummary(BaseModel):
    id: str
    name: str
    description: str = ""
    n_codes: int


class CodeSummary(BaseModel):
    id: str
    parameter_id: str
    name: str
    description: str = ""


class LanguageColumn(BaseModel):
    name: str
    dtype: str
    n_unique: int
    sample_values: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# estimator specification
# ---------------------------------------------------------------------------


class EstimatorSpec(BaseModel):
    """Serializable estimator specification.

    Mirrors the ``typola.estimators`` factory functions by name + params.
    """

    name: Literal[
        "mle",
        "laplace",
        "jeffreys",
        "dirichlet",
        "empirical_bayes",
        "uniform",
    ]
    params: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# query request
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    typology: str = "wals"
    target: str
    given: Optional[str] = None
    given_value: Optional[str] = None
    condition: dict[str, Union[str, list[str]]] = Field(default_factory=dict)
    parameter_conditions: dict[str, Union[str, list[str]]] = Field(default_factory=dict)
    estimator: EstimatorSpec = Field(
        default_factory=lambda: EstimatorSpec(name="jeffreys")
    )


# ---------------------------------------------------------------------------
# query result
# ---------------------------------------------------------------------------


class SupportItem(BaseModel):
    id: str
    name: str
    count: int
    probability: float


class DistributionResult(BaseModel):
    kind: Literal["distribution"] = "distribution"
    target_id: str
    target_name: str
    typology: str
    support: list[SupportItem]
    n_observations: int
    entropy_bits: float
    normalized_entropy: float
    mode_id: str
    mode_name: str
    estimator_name: str
    estimator_params: dict[str, Any] = Field(default_factory=dict)
    condition: dict[str, Any] = Field(default_factory=dict)
    parameter_conditions: dict[str, Any] = Field(default_factory=dict)


class ConditionalResult(BaseModel):
    kind: Literal["conditional"] = "conditional"
    target_id: str
    target_name: str
    given_id: str
    given_name: str
    typology: str
    # rows = given codes, cols = target codes
    rows: list[CodeSummary]
    cols: list[CodeSummary]
    cell_probabilities: list[list[float]]
    cell_counts: list[list[int]]
    row_totals: list[int]
    mutual_information_bits: float
    n_observations: int
    estimator_name: str
    estimator_params: dict[str, Any] = Field(default_factory=dict)
    condition: dict[str, Any] = Field(default_factory=dict)
    parameter_conditions: dict[str, Any] = Field(default_factory=dict)


QueryResult = Union[DistributionResult, ConditionalResult]


# ---------------------------------------------------------------------------
# compare estimators
# ---------------------------------------------------------------------------


class CompareEstimatorsRequest(BaseModel):
    typology: str = "wals"
    target: str
    condition: dict[str, Union[str, list[str]]] = Field(default_factory=dict)
    parameter_conditions: dict[str, Union[str, list[str]]] = Field(default_factory=dict)
    estimators: list[EstimatorSpec]


class CompareEstimatorsRow(BaseModel):
    id: str
    name: str
    count: int
    probabilities: dict[str, float]  # estimator_label → probability


class CompareEstimatorsResult(BaseModel):
    target_id: str
    target_name: str
    estimator_labels: list[str]
    rows: list[CompareEstimatorsRow]


# ---------------------------------------------------------------------------
# cross-validate
# ---------------------------------------------------------------------------


class CrossValidateRequest(BaseModel):
    typology: str = "wals"
    target: str
    condition: dict[str, Union[str, list[str]]] = Field(default_factory=dict)
    parameter_conditions: dict[str, Union[str, list[str]]] = Field(default_factory=dict)
    estimators: list[EstimatorSpec]
    n_folds: int = 5
    random_state: int = 0


class CrossValidateRow(BaseModel):
    label: str
    log_likelihood: float
    perplexity: float
    kl_to_empirical: float


class CrossValidateResult(BaseModel):
    target_id: str
    rows: list[CrossValidateRow]  # sorted by log_likelihood desc


# ---------------------------------------------------------------------------
# rank associations
# ---------------------------------------------------------------------------


class RankAssociationsRequest(BaseModel):
    typology: str = "wals"
    target: str
    condition: dict[str, Union[str, list[str]]] = Field(default_factory=dict)
    parameter_conditions: dict[str, Union[str, list[str]]] = Field(default_factory=dict)
    top_k: int = 10
    min_observations: int = 30
    estimator: EstimatorSpec = Field(
        default_factory=lambda: EstimatorSpec(name="laplace", params={"alpha": 0.5})
    )


class AssociationRow(BaseModel):
    parameter_id: str
    parameter_name: str
    mutual_information_bits: float
    n_languages: int


class RankAssociationsResult(BaseModel):
    target_id: str
    target_name: str
    rows: list[AssociationRow]
