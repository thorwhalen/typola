/**
 * Renders a Distribution as a sortable horizontal-bar list.
 *
 * Each row is clickable → creates a new drill query that adds this code as
 * a parameter_condition for the next question. That's the core drill mechanic.
 */
import { ArrowRight } from "lucide-react";
import { useMemo } from "react";
import type { DistributionResult } from "@/lib/schemas";
import { cn, fmtInt, fmtProb } from "@/lib/utils";

interface Props {
  result: DistributionResult;
  onDrill?: (codeId: string, codeName: string) => void;
}

export function DistributionView({ result, onDrill }: Props) {
  const sorted = useMemo(
    () => [...result.support].sort((a, b) => b.probability - a.probability),
    [result.support],
  );
  const maxP = sorted.length > 0 ? sorted[0].probability : 1;
  const sum = result.n_observations;

  return (
    <div className="space-y-1">
      {sorted.map((row) => {
        const pctOfMax = (row.probability / Math.max(maxP, 1e-9)) * 100;
        const clickable = !!onDrill;
        return (
          <div
            key={row.id}
            onClick={clickable ? () => onDrill!(row.id, row.name) : undefined}
            className={cn(
              "group relative grid grid-cols-[8rem_1fr_7rem] items-center gap-3 rounded-md px-2 py-1.5 text-sm",
              clickable &&
                "cursor-pointer hover:bg-accent/40 focus:bg-accent/50 focus:outline-none",
            )}
            role={clickable ? "button" : undefined}
            tabIndex={clickable ? 0 : undefined}
          >
            <div className="flex min-w-0 items-center gap-2">
              <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                {row.id}
              </span>
              <span className="truncate font-medium">{row.name || "—"}</span>
            </div>

            <div className="relative h-4 overflow-hidden rounded bg-muted">
              <div
                className="h-full rounded bg-foreground/80"
                style={{ width: `${Math.max(pctOfMax, 0.5)}%` }}
              />
            </div>

            <div className="flex items-center justify-end gap-3 tabular-nums">
              <span className="text-xs text-muted-foreground">
                {row.count > 0 ? fmtInt(row.count) : "0"}
              </span>
              <span className="w-14 text-right font-mono text-xs font-medium">
                {fmtProb(row.probability)}
              </span>
              {clickable && (
                <ArrowRight className="h-3 w-3 opacity-0 transition-opacity group-hover:opacity-60" />
              )}
            </div>
          </div>
        );
      })}
      {sum === 0 && (
        <p className="px-2 py-2 text-xs text-muted-foreground">
          No observations under this filter. Values shown are pure prior.
        </p>
      )}
    </div>
  );
}
