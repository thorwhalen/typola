/**
 * Conditional Probability Table rendered as a heatmap with values.
 *
 * Rows = values of "given" parameter, columns = values of "target".
 * Each cell shows the probability; hue intensity encodes magnitude.
 * Clicking a row header → drills into the Distribution for that given value.
 */
import { useMemo } from "react";
import type { ConditionalResult } from "@/lib/schemas";
import { cn, fmtInt, fmtProb } from "@/lib/utils";

interface Props {
  result: ConditionalResult;
  onDrillRow?: (givenId: string, givenName: string) => void;
}

export function CPTView({ result, onDrillRow }: Props) {
  const { rows, cols, cell_probabilities, cell_counts, row_totals } = result;

  const maxCell = useMemo(
    () => Math.max(...cell_probabilities.flat(), 1e-9),
    [cell_probabilities],
  );

  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full border-collapse text-xs">
        <thead className="bg-muted/60">
          <tr>
            <th className="sticky left-0 z-10 min-w-[10rem] border-r border-b bg-muted/60 p-2 text-left font-semibold text-muted-foreground">
              <span className="font-mono text-[10px]">{result.given_id}</span>
              <span className="block truncate text-[11px] normal-case text-foreground">
                {result.given_name}
              </span>
            </th>
            {cols.map((c) => (
              <th
                key={c.id}
                className="border-b border-l p-2 text-center align-bottom"
                title={c.description || c.name}
              >
                <div className="rounded bg-background px-1 py-0.5 font-mono text-[10px] text-muted-foreground">
                  {c.id}
                </div>
                <div className="mt-0.5 whitespace-nowrap text-[11px] font-medium">
                  {c.name || "—"}
                </div>
              </th>
            ))}
            <th className="w-16 border-b border-l p-2 text-right align-bottom text-[10px] font-medium uppercase text-muted-foreground">
              n
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id}>
              <th
                scope="row"
                onClick={onDrillRow ? () => onDrillRow(r.id, r.name) : undefined}
                className={cn(
                  "sticky left-0 z-10 min-w-[10rem] border-r border-b bg-background p-2 text-left align-top",
                  onDrillRow && "cursor-pointer hover:bg-accent/30",
                )}
              >
                <div className="flex items-center gap-1.5">
                  <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                    {r.id}
                  </span>
                  <span className="truncate text-[11px] font-medium">
                    {r.name || "—"}
                  </span>
                </div>
              </th>
              {cols.map((c, j) => {
                const p = cell_probabilities[i][j];
                const n = cell_counts[i][j];
                const intensity = Math.min(p / maxCell, 1);
                return (
                  <td
                    key={c.id}
                    className="relative border-b border-l text-center align-middle"
                    title={`p=${p.toFixed(4)}, n=${n}`}
                  >
                    <div
                      className="absolute inset-0 bg-foreground/80"
                      style={{ opacity: intensity * 0.22 }}
                    />
                    <div className="relative flex flex-col items-center py-1.5 font-mono tabular-nums">
                      <span
                        className={cn(
                          "text-[12px]",
                          p > 0.5 ? "font-semibold" : "font-normal",
                        )}
                      >
                        {fmtProb(p, 2)}
                      </span>
                      {n > 0 && (
                        <span className="text-[9px] text-muted-foreground">
                          {fmtInt(n)}
                        </span>
                      )}
                    </div>
                  </td>
                );
              })}
              <td className="border-b border-l p-2 text-right text-[11px] tabular-nums text-muted-foreground">
                {fmtInt(row_totals[i])}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
