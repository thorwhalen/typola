/**
 * semix — probability console.
 *
 * Layout:
 *   ┌──────────────────────────────────────────────────────────────┐
 *   │  semix   [typology picker]                    [theme] [GH]   │
 *   ├──────────────────┬─────────────────────────┬─────────────────┤
 *   │                  │                         │                  │
 *   │  Query builder   │   Results stream        │  History        │
 *   │  (left, 340px)   │   (scroll)              │  (right, zodal) │
 *   │                  │                         │                  │
 *   └──────────────────┴─────────────────────────┴─────────────────┘
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Github, Moon, Sun } from "lucide-react";

import type { QueryRequest, QueryResult, QueryRun } from "@/lib/schemas";
import { runQuery } from "@/lib/api";
import { makeTitle, useSession } from "@/stores/session";
import {
  addHistoryRecord,
  useHistoryCollection,
  type QueryRunRecord,
} from "@/stores/historyCollection";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { QueryBuilder } from "@/components/QueryBuilder";
import { ResultCard } from "@/components/ResultCard";
import { TypologyPicker } from "@/components/TypologyPicker";
import { ExamplesStrip } from "@/components/ExamplesStrip";
import { HistorySidebar } from "@/components/HistorySidebar";

function genId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function App() {
  const { setPending, typology } = useSession();
  const historyState = useHistoryCollection() as any;
  const historyItems: QueryRunRecord[] = historyState.items ?? historyState.data ?? [];

  const [isPending, setIsPending] = useState(false);
  const [dark, setDark] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // The results pane shows an ephemeral "current session" stream, which is
  // the last N runs since the page loaded. History (persistent) is the
  // right-hand panel powered by zodal. This distinction keeps the scroll
  // stream focused on the current exploration.
  const [sessionRuns, setSessionRuns] = useState<QueryRun[]>([]);

  const commitRun = useCallback(
    async (request: QueryRequest, result: QueryResult) => {
      const title = makeTitle(request, result);
      const run: QueryRun = {
        id: genId(),
        created_at: new Date().toISOString(),
        request,
        title,
        result,
      };
      setSessionRuns((s) => [run, ...s].slice(0, 30));
      // Also persist to the zodal-backed history.
      const rec: QueryRunRecord = {
        id: run.id,
        created_at: run.created_at,
        typology: request.typology,
        title,
        target_id: request.target,
        target_name: "target_name" in result ? result.target_name : request.target,
        given_id: result.kind === "conditional" ? result.given_id : "",
        kind: result.kind,
        estimator: labelEstimator(request.estimator),
        n_observations: result.n_observations,
        entropy_bits: result.kind === "distribution" ? result.entropy_bits : 0,
        mutual_information_bits:
          result.kind === "conditional" ? result.mutual_information_bits : 0,
        payload_json: JSON.stringify({ request, result }),
      };
      try {
        await addHistoryRecord(rec);
      } catch (e) {
        console.warn("history persist failed", e);
      }
    },
    [],
  );

  const runRequest = useCallback(
    async (req: QueryRequest) => {
      setPending((p) => ({ ...p, ...req }));
      setIsPending(true);
      try {
        const result = await runQuery(req);
        await commitRun(req, result);
        setError(null);
      } catch (e: any) {
        setError(String(e?.message || e));
      } finally {
        setIsPending(false);
      }
    },
    [commitRun, setPending],
  );

  const openFromHistory = useCallback((req: QueryRequest, res: QueryResult) => {
    setPending((p) => ({ ...p, ...req }));
    const run: QueryRun = {
      id: genId(),
      created_at: new Date().toISOString(),
      request: req,
      title: makeTitle(req, res),
      result: res,
    };
    setSessionRuns((s) => [run, ...s.filter((r) => r.id !== run.id)].slice(0, 30));
  }, [setPending]);

  const toggleDark = () => {
    document.documentElement.classList.toggle("dark");
    setDark((d) => !d);
  };

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Top bar */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b px-4">
        <div className="flex items-center gap-4">
          <a href="/" className="flex items-center gap-2">
            <span className="inline-block h-5 w-5 rounded-md bg-gradient-to-br from-indigo-500 via-fuchsia-500 to-amber-400" />
            <span className="text-sm font-semibold tracking-tight">semix</span>
            <span className="ml-1 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium uppercase text-muted-foreground">
              probability console
            </span>
          </a>
          <Separator orientation="vertical" className="hidden h-6 md:block" />
          <TypologyPicker />
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={toggleDark}
            title="Toggle theme"
          >
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            asChild
            title="semix on GitHub"
          >
            <a
              href="https://github.com/thorwhalen/semix"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Github className="h-4 w-4" />
            </a>
          </Button>
        </div>
      </header>

      {/* Main */}
      <div className="flex flex-1 overflow-hidden">
        <aside className="hidden w-[360px] shrink-0 border-r md:block">
          <QueryBuilder
            isPending={isPending}
            onRun={commitRun}
            onError={setError}
            setPendingFlag={setIsPending}
          />
        </aside>

        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="mx-auto max-w-4xl space-y-4 p-6">
            {error && (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            )}

            {sessionRuns.length === 0 ? (
              <div className="space-y-6 py-4">
                <div>
                  <h1 className="text-xl font-semibold">
                    Interrogate a typology probabilistically
                  </h1>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Ask a probability question on the left — or pick an example below.
                    Click any row in a result to drill into a new question.
                  </p>
                </div>
                <ExamplesStrip typology={typology} onPick={runRequest} />
              </div>
            ) : (
              <div className="space-y-5">
                {sessionRuns.map((run, i) => (
                  <ResultCard
                    key={run.id}
                    run={run}
                    index={sessionRuns.length - 1 - i}
                    onDrill={runRequest}
                    onDelete={(id) =>
                      setSessionRuns((s) => s.filter((r) => r.id !== id))
                    }
                  />
                ))}
              </div>
            )}
          </div>
        </main>

        <aside className="hidden w-[320px] shrink-0 border-l lg:block">
          <HistorySidebar onOpen={openFromHistory} />
        </aside>
      </div>
    </div>
  );
}

function labelEstimator(est: QueryRequest["estimator"]): string {
  if (!est) return "jeffreys";
  const entries = Object.entries(est.params || {});
  if (!entries.length) return est.name;
  return `${est.name}(${entries.map(([k, v]) => `${k}=${v}`).join(", ")})`;
}
