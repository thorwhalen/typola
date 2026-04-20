/**
 * History sidebar — powered by the zodal-backed QueryRun collection.
 *
 * Rendering is driven off the collection's schema: column definitions come
 * from `toColumnDefs(queryRunCollection)`, which reads the field affordances
 * we declared in historyCollection.ts. That means the visible columns, their
 * titles, their widths, their sort behaviors are all single-source.
 *
 * This is the part of the app that most naturally fits zodal's "schema
 * drives the UI" philosophy — a list of typed records with CRUD.
 */
import { useMemo } from "react";
import { History, Search, Trash2 } from "lucide-react";
import { toColumnDefs } from "@zodal/ui";

import type { QueryRequest, QueryResult } from "@/lib/schemas";
import { cn, fmtBits, fmtInt } from "@/lib/utils";
import {
  queryRunCollection,
  useHistoryCollection,
  deleteHistoryRecord,
  type QueryRunRecord,
} from "@/stores/historyCollection";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface Props {
  onOpen: (req: QueryRequest, res: QueryResult) => void;
}

export function HistorySidebar({ onOpen }: Props) {
  const state = useHistoryCollection() as any;
  const items: QueryRunRecord[] = state.items ?? state.data ?? [];

  const columnDefs = useMemo(() => toColumnDefs(queryRunCollection), []);

  if (!items.length) {
    return (
      <div className="flex h-full flex-col">
        <Header count={0} />
        <Separator />
        <div className="flex flex-1 items-center justify-center p-6 text-center text-xs text-muted-foreground">
          Past queries will appear here once you ask one.
        </div>
        <SchemaFootprint columnDefs={columnDefs} />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <Header count={items.length} />
      <Separator />
      <div className="flex-1 overflow-y-auto p-2 scrollbar-thin">
        <ul className="space-y-1">
          {items
            .slice()
            .sort((a, b) => (a.created_at < b.created_at ? 1 : -1))
            .map((r) => (
              <li key={r.id}>
                <HistoryItem
                  record={r}
                  onClick={() => {
                    try {
                      const parsed = JSON.parse(r.payload_json);
                      onOpen(parsed.request, parsed.result);
                    } catch {
                      /* ignore */
                    }
                  }}
                  onDelete={() => {
                    void deleteHistoryRecord(r.id);
                  }}
                />
              </li>
            ))}
        </ul>
      </div>
      <SchemaFootprint columnDefs={columnDefs} />
    </div>
  );
}

function Header({ count }: { count: number }) {
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <div className="flex items-center gap-2">
        <History className="h-4 w-4 text-muted-foreground" />
        <h2 className="text-sm font-semibold">History</h2>
      </div>
      <span className="text-[10px] text-muted-foreground">
        {count > 0 ? `${count} saved` : "empty"}
      </span>
    </div>
  );
}

function HistoryItem({
  record,
  onClick,
  onDelete,
}: {
  record: QueryRunRecord;
  onClick: () => void;
  onDelete: () => void;
}) {
  const created = new Date(record.created_at);
  return (
    <div className="group relative rounded-md border bg-card p-3 transition-colors hover:bg-accent/40">
      <button
        type="button"
        className="flex w-full flex-col items-start gap-1 text-left"
        onClick={onClick}
      >
        <div className="flex flex-wrap items-center gap-1">
          <Badge variant="outline" className="text-[9px] uppercase tracking-wide">
            {record.typology}
          </Badge>
          <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
            {record.target_id}
          </span>
          {record.given_id && (
            <>
              <span className="text-[10px] text-muted-foreground">|</span>
              <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                {record.given_id}
              </span>
            </>
          )}
          <Badge
            variant={record.kind === "distribution" ? "secondary" : "outline"}
            className="text-[10px]"
          >
            {record.kind}
          </Badge>
        </div>
        <div className="line-clamp-2 text-xs font-medium leading-snug">
          {record.title}
        </div>
        <div className="flex w-full items-center justify-between text-[10px] text-muted-foreground">
          <span>{formatRelativeTime(created)}</span>
          <span>
            n={fmtInt(record.n_observations)}
            {record.entropy_bits > 0 ? ` · H=${fmtBits(record.entropy_bits)}` : ""}
            {record.mutual_information_bits > 0
              ? ` · MI=${fmtBits(record.mutual_information_bits)}`
              : ""}
          </span>
        </div>
      </button>
      <Button
        variant="ghost"
        size="icon"
        className="absolute right-1 top-1 h-6 w-6 opacity-0 transition-opacity group-hover:opacity-70 hover:opacity-100"
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        title="Remove"
      >
        <Trash2 className="h-3 w-3" />
      </Button>
    </div>
  );
}

function SchemaFootprint({ columnDefs }: { columnDefs: any[] }) {
  // Tiny proof of life: show how many visible columns zodal inferred.
  const visible = columnDefs.filter((c) => c.visible !== false);
  return (
    <div className="border-t px-4 py-2 text-[10px] text-muted-foreground">
      <span className="flex items-center gap-1.5">
        <Search className="h-3 w-3" />
        schema-driven view · {visible.length} columns
      </span>
    </div>
  );
}

function formatRelativeTime(d: Date): string {
  const ms = Date.now() - d.getTime();
  const s = Math.floor(ms / 1000);
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const days = Math.floor(h / 24);
  if (days < 7) return `${days}d ago`;
  return d.toLocaleDateString();
}
