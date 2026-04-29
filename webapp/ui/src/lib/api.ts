/**
 * Thin fetch wrapper over the FastAPI backend.
 * All functions return zod-validated objects.
 *
 * The API base URL is read from the build-time env var `VITE_API_BASE`
 * (default `/api`). This lets the same SPA be mounted at any URL prefix:
 *
 *   - Local dev (Vite proxies):        VITE_API_BASE unset → `/api`
 *   - Enlace at /api/{name}:           VITE_API_BASE=/api/typola
 *   - Standalone under custom prefix:  VITE_API_BASE=/whatever
 *
 * No deployment path is hard-coded in the app.
 */
import {
  CompareEstimatorsResult,
  CrossValidateResult,
  CodeSummary,
  LanguageColumn,
  ParameterSummary,
  QueryRequest,
  QueryResult,
  RankAssociationsResult,
  TypologySummary,
} from "./schemas";

const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/$/, "");

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const url = API_BASE + (path.startsWith("/") ? path : `/${path}`);
  const r = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!r.ok) {
    const detail = await r.text().catch(() => r.statusText);
    throw new Error(`${r.status} ${url}: ${detail}`);
  }
  return (await r.json()) as T;
}

// ---- metadata ---------------------------------------------------------------

export async function listTypologies() {
  const raw = await json<unknown[]>("/typologies");
  return raw.map((r) => TypologySummary.parse(r));
}

export async function listParameters(typology: string) {
  const raw = await json<unknown[]>(
    `/typologies/${encodeURIComponent(typology)}/parameters`,
  );
  return raw.map((r) => ParameterSummary.parse(r));
}

export async function listCodes(typology: string, parameterId: string) {
  const raw = await json<unknown[]>(
    `/typologies/${encodeURIComponent(typology)}/parameters/${encodeURIComponent(parameterId)}/codes`,
  );
  return raw.map((r) => CodeSummary.parse(r));
}

export async function listLanguageColumns(typology: string) {
  const raw = await json<unknown[]>(
    `/typologies/${encodeURIComponent(typology)}/languages/columns`,
  );
  return raw.map((r) => LanguageColumn.parse(r));
}

export async function listColumnValues(typology: string, column: string, limit = 500) {
  return await json<string[]>(
    `/typologies/${encodeURIComponent(typology)}/languages/values?column=${encodeURIComponent(column)}&limit=${limit}`,
  );
}

// ---- core query -------------------------------------------------------------

export async function runQuery(req: QueryRequest): Promise<QueryResult> {
  const body = QueryRequest.parse(req);
  const raw = await json<unknown>("/query", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return QueryResult.parse(raw);
}

// ---- compare ----------------------------------------------------------------

export async function compareEstimators(body: {
  typology: string;
  target: string;
  condition?: Record<string, string | string[]>;
  parameter_conditions?: Record<string, string | string[]>;
  estimators: { name: string; params?: Record<string, unknown> }[];
}): Promise<CompareEstimatorsResult> {
  const raw = await json<unknown>("/compare-estimators", {
    method: "POST",
    body: JSON.stringify({
      typology: body.typology,
      target: body.target,
      condition: body.condition || {},
      parameter_conditions: body.parameter_conditions || {},
      estimators: body.estimators.map((e) => ({ name: e.name, params: e.params || {} })),
    }),
  });
  return CompareEstimatorsResult.parse(raw);
}

export async function crossValidate(body: {
  typology: string;
  target: string;
  condition?: Record<string, string | string[]>;
  parameter_conditions?: Record<string, string | string[]>;
  estimators: { name: string; params?: Record<string, unknown> }[];
  n_folds?: number;
  random_state?: number;
}): Promise<CrossValidateResult> {
  const raw = await json<unknown>("/cross-validate", {
    method: "POST",
    body: JSON.stringify({
      typology: body.typology,
      target: body.target,
      condition: body.condition || {},
      parameter_conditions: body.parameter_conditions || {},
      estimators: body.estimators.map((e) => ({ name: e.name, params: e.params || {} })),
      n_folds: body.n_folds ?? 5,
      random_state: body.random_state ?? 0,
    }),
  });
  return CrossValidateResult.parse(raw);
}

// ---- rank associations ------------------------------------------------------

export async function rankAssociations(body: {
  typology: string;
  target: string;
  condition?: Record<string, string | string[]>;
  parameter_conditions?: Record<string, string | string[]>;
  top_k?: number;
  min_observations?: number;
}): Promise<RankAssociationsResult> {
  const raw = await json<unknown>("/rank-associations", {
    method: "POST",
    body: JSON.stringify({
      typology: body.typology,
      target: body.target,
      condition: body.condition || {},
      parameter_conditions: body.parameter_conditions || {},
      top_k: body.top_k ?? 10,
      min_observations: body.min_observations ?? 30,
      estimator: { name: "laplace", params: { alpha: 0.5 } },
    }),
  });
  return RankAssociationsResult.parse(raw);
}
