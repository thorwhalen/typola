/**
 * Zod schemas mirroring webapp/api/schemas.py.
 *
 * Kept narrowly typed so the UI compiler catches drift from the server.
 */
import { z } from "zod";

// ---- metadata ---------------------------------------------------------------

export const TypologySummary = z.object({
  name: z.string(),
  n_languages: z.number(),
  n_parameters: z.number(),
  n_codes: z.number(),
  n_values: z.number(),
  citation: z.string().default(""),
  license: z.string().default(""),
});
export type TypologySummary = z.infer<typeof TypologySummary>;

export const ParameterSummary = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().default(""),
  n_codes: z.number(),
});
export type ParameterSummary = z.infer<typeof ParameterSummary>;

export const CodeSummary = z.object({
  id: z.string(),
  parameter_id: z.string(),
  name: z.string(),
  description: z.string().default(""),
});
export type CodeSummary = z.infer<typeof CodeSummary>;

export const LanguageColumn = z.object({
  name: z.string(),
  dtype: z.string(),
  n_unique: z.number(),
  sample_values: z.array(z.string()).default([]),
});
export type LanguageColumn = z.infer<typeof LanguageColumn>;

// ---- estimator --------------------------------------------------------------

export const EstimatorName = z.enum([
  "mle",
  "laplace",
  "jeffreys",
  "dirichlet",
  "empirical_bayes",
  "uniform",
]);
export type EstimatorName = z.infer<typeof EstimatorName>;

export const EstimatorSpec = z.object({
  name: EstimatorName,
  params: z.record(z.string(), z.any()).default({}),
});
export type EstimatorSpec = z.infer<typeof EstimatorSpec>;

// ---- query request ----------------------------------------------------------

export const QueryRequest = z.object({
  typology: z.string().default("wals"),
  target: z.string(),
  given: z.string().optional(),
  given_value: z.string().optional(),
  condition: z.record(z.string(), z.union([z.string(), z.array(z.string())])).default({}),
  parameter_conditions: z
    .record(z.string(), z.union([z.string(), z.array(z.string())]))
    .default({}),
  estimator: EstimatorSpec.default({ name: "jeffreys", params: {} }),
});
export type QueryRequest = z.infer<typeof QueryRequest>;

// ---- query result -----------------------------------------------------------

export const SupportItem = z.object({
  id: z.string(),
  name: z.string(),
  count: z.number(),
  probability: z.number(),
});
export type SupportItem = z.infer<typeof SupportItem>;

export const DistributionResult = z.object({
  kind: z.literal("distribution"),
  target_id: z.string(),
  target_name: z.string(),
  typology: z.string(),
  support: z.array(SupportItem),
  n_observations: z.number(),
  entropy_bits: z.number(),
  normalized_entropy: z.number(),
  mode_id: z.string(),
  mode_name: z.string(),
  estimator_name: z.string(),
  estimator_params: z.record(z.string(), z.any()).default({}),
  condition: z.record(z.string(), z.any()).default({}),
  parameter_conditions: z.record(z.string(), z.any()).default({}),
});
export type DistributionResult = z.infer<typeof DistributionResult>;

export const ConditionalResult = z.object({
  kind: z.literal("conditional"),
  target_id: z.string(),
  target_name: z.string(),
  given_id: z.string(),
  given_name: z.string(),
  typology: z.string(),
  rows: z.array(CodeSummary),
  cols: z.array(CodeSummary),
  cell_probabilities: z.array(z.array(z.number())),
  cell_counts: z.array(z.array(z.number())),
  row_totals: z.array(z.number()),
  mutual_information_bits: z.number(),
  n_observations: z.number(),
  estimator_name: z.string(),
  estimator_params: z.record(z.string(), z.any()).default({}),
  condition: z.record(z.string(), z.any()).default({}),
  parameter_conditions: z.record(z.string(), z.any()).default({}),
});
export type ConditionalResult = z.infer<typeof ConditionalResult>;

export const QueryResult = z.discriminatedUnion("kind", [
  DistributionResult,
  ConditionalResult,
]);
export type QueryResult = z.infer<typeof QueryResult>;

// ---- compare estimators -----------------------------------------------------

export const CompareEstimatorsResult = z.object({
  target_id: z.string(),
  target_name: z.string(),
  estimator_labels: z.array(z.string()),
  rows: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      count: z.number(),
      probabilities: z.record(z.string(), z.number()),
    }),
  ),
});
export type CompareEstimatorsResult = z.infer<typeof CompareEstimatorsResult>;

// ---- cross-validate ---------------------------------------------------------

export const CrossValidateResult = z.object({
  target_id: z.string(),
  rows: z.array(
    z.object({
      label: z.string(),
      log_likelihood: z.number(),
      perplexity: z.number(),
      kl_to_empirical: z.number(),
    }),
  ),
});
export type CrossValidateResult = z.infer<typeof CrossValidateResult>;

// ---- rank associations ------------------------------------------------------

export const RankAssociationsResult = z.object({
  target_id: z.string(),
  target_name: z.string(),
  rows: z.array(
    z.object({
      parameter_id: z.string(),
      parameter_name: z.string(),
      mutual_information_bits: z.number(),
      n_languages: z.number(),
    }),
  ),
});
export type RankAssociationsResult = z.infer<typeof RankAssociationsResult>;

// ---- query history (client-side, via zodal) --------------------------------

export const QueryRun = z.object({
  id: z.string(),
  created_at: z.string(),
  request: QueryRequest,
  title: z.string(),
  result: QueryResult,
});
export type QueryRun = z.infer<typeof QueryRun>;
