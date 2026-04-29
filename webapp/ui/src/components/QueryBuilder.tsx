/**
 * The query builder — a stable panel on the left of the app.
 *
 * Layout:
 *   Ask: [target]
 *   Given: [+ given parameter]  (optional)
 *   Where: [chips]              (language + parameter conditions)
 *   Using: [estimator]
 *   [Ask] (Cmd+Enter)
 */
import { useCallback } from "react";
import { CornerDownLeft, RotateCcw, Sparkles } from "lucide-react";

import type { QueryRequest, QueryResult } from "@/lib/schemas";
import { runQuery } from "@/lib/api";
import { makeTitle, useSession } from "@/stores/session";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ParameterPicker } from "./ParameterPicker";
import { FilterChips } from "./FilterChips";
import { EstimatorPicker } from "./EstimatorPicker";
import { ExamplesStrip } from "./ExamplesStrip";

interface Props {
  isPending: boolean;
  onRun: (req: QueryRequest, result: QueryResult) => void;
  onError: (msg: string) => void;
  setPendingFlag: (v: boolean) => void;
}

export function QueryBuilder({ isPending, onRun, onError, setPendingFlag }: Props) {
  const { pending, setPending, resetPending, typology } = useSession();

  const canAsk = !!pending.target && !isPending;

  const ask = useCallback(async () => {
    if (!canAsk) return;
    const req: QueryRequest = {
      typology: pending.typology || typology,
      target: pending.target,
      given: pending.given || undefined,
      given_value: pending.given_value || undefined,
      condition: pending.condition || {},
      parameter_conditions: pending.parameter_conditions || {},
      estimator: pending.estimator,
    };
    setPendingFlag(true);
    try {
      const result = await runQuery(req);
      onRun(req, result);
    } catch (e: any) {
      onError(String(e?.message || e));
    } finally {
      setPendingFlag(false);
    }
  }, [canAsk, pending, typology, onRun, onError, setPendingFlag]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        ask();
      }
    },
    [ask],
  );

  return (
    <div className="flex h-full flex-col" onKeyDown={handleKeyDown}>
      <div className="px-4 py-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold">Ask typola</h2>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Build a probability question. Press{" "}
          <kbd className="rounded border bg-muted px-1 font-mono text-[10px]">⌘↵</kbd> to run.
        </p>
      </div>

      <Separator />

      <div className="flex flex-1 flex-col gap-5 overflow-y-auto px-4 py-4 scrollbar-thin">
        {/* Target */}
        <Field label="Ask about" hint="The parameter whose probability you want.">
          <ParameterPicker
            typology={typology}
            value={pending.target || undefined}
            onChange={(id) =>
              setPending((p) => ({ ...p, target: id || "" }))
            }
          />
        </Field>

        {/* Given */}
        <Field
          label="Given (optional)"
          hint="Condition on another parameter to build a conditional distribution."
        >
          <ParameterPicker
            typology={typology}
            value={pending.given || undefined}
            onChange={(id) =>
              setPending((p) => ({
                ...p,
                given: id,
                given_value: undefined,
              }))
            }
            placeholder="(skip)"
            allowClear
          />
        </Field>

        {/* Conditions */}
        <Field
          label="Where"
          hint="Narrow the sample — by language family, macroarea, or another parameter's value."
        >
          <FilterChips
            typology={typology}
            languageConditions={pending.condition as Record<string, string>}
            parameterConditions={pending.parameter_conditions as Record<string, string>}
            onChange={({ languageConditions, parameterConditions }) =>
              setPending((p) => ({
                ...p,
                condition: languageConditions ?? p.condition,
                parameter_conditions: parameterConditions ?? p.parameter_conditions,
              }))
            }
          />
        </Field>

        {/* Estimator */}
        <Field
          label="Using"
          hint="Count → probability strategy. Jeffreys is a safe default."
        >
          <EstimatorPicker
            value={pending.estimator}
            onChange={(spec) => setPending((p) => ({ ...p, estimator: spec }))}
          />
        </Field>
      </div>

      <Separator />

      <div className="flex flex-col gap-2 p-4">
        <Button
          onClick={ask}
          disabled={!canAsk}
          className={cn("w-full gap-2", isPending && "opacity-70")}
        >
          {isPending ? "Computing…" : "Ask"}
          <CornerDownLeft className="h-4 w-4 opacity-70" />
        </Button>
        <Button
          onClick={resetPending}
          variant="ghost"
          size="sm"
          className="h-7 gap-1 text-xs text-muted-foreground"
        >
          <RotateCcw className="h-3 w-3" />
          Clear
        </Button>
      </div>
    </div>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-muted-foreground">{label}</label>
      {children}
      {hint && <p className="text-[11px] leading-snug text-muted-foreground">{hint}</p>}
    </div>
  );
}
