/**
 * A single result card. Title, metadata, primary view, action row.
 */
import { useState } from "react";
import {
  BarChart2,
  ChevronDown,
  ChevronUp,
  Copy,
  Gauge,
  LineChart as LineChartIcon,
  Scale,
  Trash2,
} from "lucide-react";
import { useMutation } from "@tanstack/react-query";

import type { QueryRequest, QueryRun } from "@/lib/schemas";
import { makeTitle, useSession } from "@/stores/session";
import { runQuery, compareEstimators, crossValidate, rankAssociations } from "@/lib/api";
import { cn, fmtBits, fmtInt, fmtProb } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { DistributionView } from "./DistributionView";
import { CPTView } from "./CPTView";
import { ESTIMATOR_PRESETS } from "./EstimatorPicker";

interface Props {
  run: QueryRun;
  onDrill: (next: QueryRequest) => void;
  onDelete?: (id: string) => void;
  index: number;
}

export function ResultCard({ run, onDrill, onDelete, index }: Props) {
  const { request, result } = run;
  const [extras, setExtras] = useState<null | "compare" | "cv" | "rank">(null);

  const drill = (pid: string, codeId: string) => {
    const next: QueryRequest = {
      ...request,
      parameter_conditions: { ...request.parameter_conditions, [pid]: codeId },
    };
    onDrill(next);
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader className="gap-1">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="mb-1 flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
              <span className="font-mono">#{index + 1}</span>
              <Badge variant="outline" className="font-mono text-[10px]">
                {request.typology}
              </Badge>
              <Badge variant="outline" className="gap-1 text-[10px]">
                <Gauge className="h-3 w-3" />
                {request.estimator.name}
              </Badge>
              {result.kind === "distribution" ? (
                <span className="flex items-center gap-1.5">
                  <span className="text-muted-foreground">n=</span>
                  <span className="tabular-nums">{fmtInt(result.n_observations)}</span>
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  <span className="text-muted-foreground">n=</span>
                  <span className="tabular-nums">{fmtInt(result.n_observations)}</span>
                  <span className="mx-1 text-muted-foreground">·</span>
                  <span className="text-muted-foreground">MI=</span>
                  <span className="tabular-nums">
                    {fmtBits(result.mutual_information_bits)}
                  </span>
                </span>
              )}
              {result.kind === "distribution" && (
                <>
                  <span className="mx-1 text-muted-foreground">·</span>
                  <span>
                    <span className="text-muted-foreground">H=</span>
                    <span className="tabular-nums">{fmtBits(result.entropy_bits)}</span>
                  </span>
                  <span className="mx-1 text-muted-foreground">·</span>
                  <span>
                    <span className="text-muted-foreground">mode=</span>
                    <span className="font-medium">{result.mode_name}</span>
                  </span>
                </>
              )}
            </div>
            <h3 className="text-base font-semibold leading-tight">
              {makeTitle(request, result)}
            </h3>
            <p className="mt-1 text-xs text-muted-foreground">
              {result.kind === "distribution"
                ? result.target_name
                : `${result.target_name} given ${result.given_name}`}
            </p>
          </div>
          {onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="-m-1 h-7 w-7 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-60 hover:opacity-100"
              onClick={() => onDelete(run.id)}
              title="Remove from history"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        {result.kind === "distribution" ? (
          <DistributionView
            result={result}
            onDrill={(codeId) => drill(result.target_id, codeId)}
          />
        ) : (
          <CPTView
            result={result}
            onDrillRow={(givenId) => drill(result.given_id, givenId)}
          />
        )}

        <div className="flex flex-wrap gap-1 pt-1">
          {result.kind === "distribution" && (
            <>
              <MiniToggle
                active={extras === "compare"}
                onClick={() => setExtras(extras === "compare" ? null : "compare")}
                icon={<Scale className="h-3 w-3" />}
                label="Compare estimators"
              />
              <MiniToggle
                active={extras === "cv"}
                onClick={() => setExtras(extras === "cv" ? null : "cv")}
                icon={<BarChart2 className="h-3 w-3" />}
                label="Cross-validate"
              />
              <MiniToggle
                active={extras === "rank"}
                onClick={() => setExtras(extras === "rank" ? null : "rank")}
                icon={<LineChartIcon className="h-3 w-3" />}
                label="Rank associations"
              />
            </>
          )}
          <Button
            size="sm"
            variant="ghost"
            className="h-7 gap-1 text-xs text-muted-foreground"
            onClick={() => copyAsPython(request)}
          >
            <Copy className="h-3 w-3" />
            Copy as Python
          </Button>
        </div>

        {extras === "compare" && result.kind === "distribution" && (
          <CompareEstimatorsPanel run={run} />
        )}
        {extras === "cv" && result.kind === "distribution" && (
          <CrossValidatePanel run={run} />
        )}
        {extras === "rank" && result.kind === "distribution" && (
          <RankAssociationsPanel
            run={run}
            onDrill={(pid) => {
              // Ranking a parameter opens a CPT query for it
              onDrill({ ...request, given: pid, given_value: undefined });
            }}
          />
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// mini action toggle
// ---------------------------------------------------------------------------

function MiniToggle({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <Button
      size="sm"
      variant={active ? "secondary" : "ghost"}
      className="h-7 gap-1 text-xs"
      onClick={onClick}
    >
      {icon}
      {label}
      {active ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
    </Button>
  );
}

// ---------------------------------------------------------------------------
// expandable panels
// ---------------------------------------------------------------------------

function CompareEstimatorsPanel({ run }: { run: QueryRun }) {
  const { request } = run;
  const specs = ESTIMATOR_PRESETS.filter(
    (p) => p.spec.name !== "mle" || Object.keys(request.condition || {}).length === 0,
  ).slice(0, 5);
  const specLabels = specs.map((p) => p.label);
  const specList = specs.map((p) => p.spec);

  const m = useMutation({
    mutationFn: () =>
      compareEstimators({
        typology: request.typology,
        target: request.target,
        condition: request.condition as any,
        parameter_conditions: request.parameter_conditions as any,
        estimators: specList,
      }),
  });

  return (
    <ExtraPanel
      title="P(code) under each estimator"
      loading={m.isPending}
      onLoad={() => m.mutate()}
      error={m.error ? String(m.error) : null}
    >
      {m.data && (
        <div className="overflow-x-auto rounded-md border">
          <table className="w-full text-xs">
            <thead className="bg-muted/60">
              <tr>
                <th className="p-2 text-left font-medium">value</th>
                <th className="p-2 text-right font-medium">n</th>
                {m.data.estimator_labels.map((lbl) => (
                  <th key={lbl} className="p-2 text-right font-medium">
                    {lbl}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {m.data.rows.map((row) => (
                <tr key={row.id} className="border-t">
                  <td className="p-2">
                    <span className="rounded bg-muted px-1 py-0.5 font-mono text-[10px]">
                      {row.id}
                    </span>{" "}
                    <span className="font-medium">{row.name}</span>
                  </td>
                  <td className="p-2 text-right tabular-nums">{fmtInt(row.count)}</td>
                  {m.data!.estimator_labels.map((lbl) => (
                    <td key={lbl} className="p-2 text-right font-mono tabular-nums">
                      {fmtProb(row.probabilities[lbl] ?? 0, 3)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </ExtraPanel>
  );
}

function CrossValidatePanel({ run }: { run: QueryRun }) {
  const { request } = run;
  const specs = ESTIMATOR_PRESETS.slice(0, 6).map((p) => p.spec);
  const m = useMutation({
    mutationFn: () =>
      crossValidate({
        typology: request.typology,
        target: request.target,
        condition: request.condition as any,
        parameter_conditions: request.parameter_conditions as any,
        estimators: specs,
        n_folds: 5,
        random_state: 0,
      }),
  });

  return (
    <ExtraPanel
      title="5-fold cross-validated log-likelihood — higher is better"
      loading={m.isPending}
      onLoad={() => m.mutate()}
      error={m.error ? String(m.error) : null}
    >
      {m.data && (
        <div className="overflow-x-auto rounded-md border">
          <table className="w-full text-xs">
            <thead className="bg-muted/60">
              <tr>
                <th className="p-2 text-left font-medium">estimator</th>
                <th className="p-2 text-right font-medium">log-likelihood</th>
                <th className="p-2 text-right font-medium">perplexity</th>
                <th className="p-2 text-right font-medium">KL</th>
              </tr>
            </thead>
            <tbody>
              {m.data.rows.map((r, i) => (
                <tr key={r.label} className={cn("border-t", i === 0 && "bg-accent/30")}>
                  <td className="p-2 font-medium">{r.label}</td>
                  <td className="p-2 text-right font-mono tabular-nums">
                    {r.log_likelihood.toFixed(3)}
                  </td>
                  <td className="p-2 text-right font-mono tabular-nums">
                    {r.perplexity.toFixed(3)}
                  </td>
                  <td className="p-2 text-right font-mono tabular-nums">
                    {r.kl_to_empirical.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </ExtraPanel>
  );
}

function RankAssociationsPanel({
  run,
  onDrill,
}: {
  run: QueryRun;
  onDrill: (parameterId: string) => void;
}) {
  const { request } = run;
  const m = useMutation({
    mutationFn: () =>
      rankAssociations({
        typology: request.typology,
        target: request.target,
        condition: request.condition as any,
        parameter_conditions: request.parameter_conditions as any,
        top_k: 10,
        min_observations: 30,
      }),
  });
  return (
    <ExtraPanel
      title="Parameters most informative about the target (mutual information)"
      loading={m.isPending}
      onLoad={() => m.mutate()}
      error={m.error ? String(m.error) : null}
    >
      {m.data && (
        <div className="space-y-0.5">
          {m.data.rows.map((r) => (
            <div
              key={r.parameter_id}
              className="group flex cursor-pointer items-center gap-3 rounded-md p-2 text-sm hover:bg-accent/40"
              onClick={() => onDrill(r.parameter_id)}
            >
              <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                {r.parameter_id}
              </span>
              <span className="min-w-0 flex-1 truncate font-medium">{r.parameter_name}</span>
              <span className="shrink-0 font-mono text-xs tabular-nums text-muted-foreground">
                {fmtBits(r.mutual_information_bits)}
              </span>
              <span className="shrink-0 text-[10px] tabular-nums text-muted-foreground">
                n={fmtInt(r.n_languages)}
              </span>
            </div>
          ))}
        </div>
      )}
    </ExtraPanel>
  );
}

function ExtraPanel({
  title,
  children,
  loading,
  onLoad,
  error,
}: {
  title: string;
  children: React.ReactNode;
  loading: boolean;
  onLoad: () => void;
  error: string | null;
}) {
  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold text-muted-foreground">{title}</span>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 text-xs"
          onClick={onLoad}
          disabled={loading}
        >
          {loading ? "Computing…" : "Compute"}
        </Button>
      </div>
      {error && <p className="text-xs text-destructive">{error}</p>}
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// copy as python snippet
// ---------------------------------------------------------------------------

function copyAsPython(req: QueryRequest) {
  const lines = [
    `from semix import load, query, estimators`,
    ``,
    `tp = load(${JSON.stringify(req.typology)})`,
  ];
  const estCall = estimatorSnippet(req.estimator);
  const kwargs: string[] = [`target=${JSON.stringify(req.target)}`];
  if (req.given) kwargs.push(`given=${JSON.stringify(req.given)}`);
  if (req.given_value) kwargs.push(`given_value=${JSON.stringify(req.given_value)}`);
  if (Object.keys(req.condition || {}).length)
    kwargs.push(`condition=${JSON.stringify(req.condition)}`);
  if (Object.keys(req.parameter_conditions || {}).length)
    kwargs.push(
      `parameter_conditions=${JSON.stringify(req.parameter_conditions)}`,
    );
  kwargs.push(`estimator=${estCall}`);
  lines.push(``, `result = query(tp, ${kwargs.join(", ")})`, `print(result.to_frame())`);
  navigator.clipboard.writeText(lines.join("\n")).catch(() => void 0);
}

function estimatorSnippet(spec: QueryRequest["estimator"]): string {
  switch (spec.name) {
    case "mle":
      return "estimators.mle()";
    case "jeffreys":
      return "estimators.jeffreys()";
    case "uniform":
      return "estimators.uniform()";
    case "laplace":
      return `estimators.laplace(alpha=${spec.params.alpha ?? 1.0})`;
    case "dirichlet":
      return `estimators.dirichlet(${JSON.stringify(spec.params.prior ?? "jeffreys")})`;
    case "empirical_bayes":
      return `estimators.empirical_bayes(tp.counts(${JSON.stringify(
        "",
      )}).values, strength=${spec.params.strength ?? 1.0})`;
  }
}
