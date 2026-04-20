/**
 * Session-level state: selected typology, pending query, history of runs.
 *
 * History uses zustand's persist middleware to survive reloads. Each run is
 * a QueryRun (see schemas.ts). We keep history small (latest 50) so it fits
 * comfortably in localStorage.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { EstimatorSpec, QueryRequest, QueryResult, QueryRun } from "@/lib/schemas";

export type PendingQuery = Omit<QueryRequest, "estimator"> & {
  estimator: EstimatorSpec;
};

export interface SessionState {
  typology: string;
  pending: PendingQuery;
  history: QueryRun[];

  setTypology: (name: string) => void;
  setPending: (updater: (p: PendingQuery) => PendingQuery) => void;
  resetPending: () => void;
  addRun: (run: QueryRun) => void;
  clearHistory: () => void;
}

const emptyPending = (typology: string): PendingQuery => ({
  typology,
  target: "",
  given: undefined,
  given_value: undefined,
  condition: {},
  parameter_conditions: {},
  estimator: { name: "jeffreys", params: {} },
});

export const useSession = create<SessionState>()(
  persist(
    (set) => ({
      typology: "wals",
      pending: emptyPending("wals"),
      history: [],

      setTypology: (name) =>
        set((s) => ({
          typology: name,
          pending: { ...s.pending, typology: name, target: "" },
        })),

      setPending: (updater) => set((s) => ({ pending: updater(s.pending) })),

      resetPending: () => set((s) => ({ pending: emptyPending(s.typology) })),

      addRun: (run) =>
        set((s) => ({ history: [run, ...s.history].slice(0, 50) })),

      clearHistory: () => set({ history: [] }),
    }),
    {
      name: "semix.session.v1",
      partialize: (s) => ({ typology: s.typology, history: s.history }),
    },
  ),
);

export function makeTitle(req: QueryRequest, res: QueryResult): string {
  const parts: string[] = [];
  const label =
    "target_name" in res && res.target_name
      ? `${res.target_id} ${res.target_name}`
      : req.target;
  if (res.kind === "distribution") {
    parts.push(`P(${label})`);
  } else {
    parts.push(`P(${label} | ${res.given_id} ${res.given_name})`);
  }
  const conds: string[] = [];
  for (const [k, v] of Object.entries(req.condition || {})) {
    const vv = Array.isArray(v) ? v.join("|") : v;
    conds.push(`${k}=${vv}`);
  }
  for (const [k, v] of Object.entries(req.parameter_conditions || {})) {
    const vv = Array.isArray(v) ? v.join("|") : v;
    conds.push(`${k}=${vv}`);
  }
  if (conds.length) parts.push(`where ${conds.join(", ")}`);
  parts.push(`— ${req.estimator.name}`);
  return parts.join(" ");
}
