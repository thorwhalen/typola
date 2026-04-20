/**
 * Zodal-backed query-run history.
 *
 * We define a `QueryRunRecord` zod schema and wrap it in a zodal Collection
 * so the history can be rendered by a schema-driven UI (column defs generated
 * via zodal-ui, not hand-written) and persisted via zodal-store-localstorage.
 *
 * This proves the zodal integration on a collection that actually changes at
 * runtime (unlike the reference-data HTTP collections, which are essentially
 * read-only server projections).
 */
import { z } from "zod";
import { defineCollection } from "@zodal/core";
import { createZustandStoreSlice } from "@zodal/ui";
import { createLocalStorageProvider } from "@zodal/store-localstorage";
import { create } from "zustand";

// ---- schema ----------------------------------------------------------------

/**
 * Shape of a saved query run — the flat projection used by the history view.
 *
 * Fields marked as `storageRole: "content"` are opaque blobs the list view
 * doesn't need to show; they live in a separate field but still travel with
 * the record in our simple localStorage setup (no bifurcation here).
 */
export const QueryRunRecord = z.object({
  id: z.string(),
  created_at: z.string(),
  typology: z.string(),
  title: z.string(),
  target_id: z.string(),
  target_name: z.string(),
  given_id: z.string().optional().default(""),
  kind: z.enum(["distribution", "conditional"]),
  estimator: z.string(),
  n_observations: z.number(),
  entropy_bits: z.number().optional().default(0),
  mutual_information_bits: z.number().optional().default(0),
  /** Serialized QueryRequest + QueryResult; opaque in the list view. */
  payload_json: z.string(),
});
export type QueryRunRecord = z.infer<typeof QueryRunRecord>;

// ---- zodal collection definition --------------------------------------------

export const queryRunCollection = defineCollection(QueryRunRecord, {
  idField: "id",
  labelField: "title",
  fields: {
    id: { visible: false },
    created_at: {
      title: "When",
      sortable: "desc",
      columnWidth: 160,
    },
    typology: { title: "Source", columnWidth: 80 },
    title: {
      title: "Question",
      searchable: true,
      columnWidth: 320,
    },
    target_id: { title: "Target", columnWidth: 72 },
    target_name: { visible: false },
    given_id: { title: "Given", columnWidth: 72 },
    kind: {
      title: "Kind",
      columnWidth: 100,
      badge: { distribution: "secondary", conditional: "outline" },
    },
    estimator: { title: "Estimator", columnWidth: 130 },
    n_observations: { title: "n", columnWidth: 70 },
    entropy_bits: { title: "H (bits)", columnWidth: 80 },
    mutual_information_bits: { title: "MI (bits)", columnWidth: 80 },
    payload_json: {
      storageRole: "content",
      visible: false,
      hidden: true,
    },
  },
});

// ---- provider + zustand slice ----------------------------------------------

const provider = createLocalStorageProvider<QueryRunRecord>({
  storageKey: "semix.history.v1",
  idField: "id",
  searchFields: ["title", "target_id", "target_name", "typology", "given_id"],
});

export const useHistoryCollection = create(
  createZustandStoreSlice<QueryRunRecord>(queryRunCollection, provider),
);

// Fire an initial fetch on module load so the UI has the persisted items.
// The createZustandStoreSlice exposes a `fetchData` action.
Promise.resolve().then(() => {
  const api = useHistoryCollection.getState() as any;
  if (typeof api.fetchData === "function") api.fetchData();
});

// ---- convenience helpers ---------------------------------------------------

export async function addHistoryRecord(rec: QueryRunRecord) {
  const api = useHistoryCollection.getState() as any;
  if (typeof api.createItem === "function") {
    await api.createItem(rec);
  } else if (typeof api.provider?.create === "function") {
    await api.provider.create(rec);
    if (typeof api.fetchData === "function") await api.fetchData();
  }
}

export async function deleteHistoryRecord(id: string) {
  const api = useHistoryCollection.getState() as any;
  if (typeof api.deleteItem === "function") {
    await api.deleteItem(id);
  } else if (typeof api.provider?.delete === "function") {
    await api.provider.delete(id);
    if (typeof api.fetchData === "function") await api.fetchData();
  }
}
