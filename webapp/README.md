# semix — probability console (webapp)

A two-process web app for exploring probabilities over typology data.

```
┌─────────────────────────────────────────────────────────────────┐
│  semix   [typology picker]                     [theme] [GH]    │
├──────────────────┬──────────────────────────┬──────────────────┤
│  Query builder   │  Results stream          │  History         │
│  (left)          │  (center, drill by clicking any row)        │
│                  │                          │  (zodal-backed)  │
└──────────────────┴──────────────────────────┴──────────────────┘
```

## Run it

### 1. Backend (FastAPI)

From the repo root:

```bash
pip install -e '.[web]'

# Point at local CLDF copies (optional; downloads on first run if omitted)
export SEMIX_TYPOLOGY_WALS_PATH=/path/to/wals-master
export SEMIX_TYPOLOGY_GRAMBANK_PATH=/path/to/grambank-1.0.3

python -m webapp.api.main
# serving on http://127.0.0.1:8765
```

### 2. Frontend (Vite + React)

In another terminal:

```bash
cd webapp/ui
npm install      # first time only
npm run dev
# open http://127.0.0.1:5173
```

The Vite dev server proxies `/api/*` to the backend at `:8765`.

## What the UX does

**Query builder (left)** — four schema-driven fields:

- **Ask about** — the target parameter. Combobox over all ~200 parameters, searchable by ID or name.
- **Given (optional)** — a second parameter for conditional probabilities (CPT mode).
- **Where** — filter chips for (a) language metadata (Family, Macroarea, …) and (b) other parameters' values. Adding a chip is a single popover: pick the dimension, pick the value.
- **Using** — the count-to-probability estimator. Presets for Jeffreys, Laplace at several α, MLE, empirical Bayes, uniform.
- **Ask** or press ⌘↵.

**Results stream (center)** — each answer is a card:

- Bar-ranked distribution (or a heatmap for CPTs).
- Click any row → drill: that code becomes a `parameter_conditions` entry in a new query.
- Per-card actions:
  - **Compare estimators** — side-by-side P(value) under Jeffreys / Laplace(α) / empirical Bayes / MLE / uniform.
  - **Cross-validate** — 5-fold held-out log-likelihood, perplexity, KL to empirical. Tells you *which* estimator is actually best for this question.
  - **Rank associations** — top mutual-information parameters to the target; click to open as a CPT.
  - **Copy as Python** — copies a snippet that reproduces the query with `semix.query(...)`.

**History sidebar (right, zodal-backed)** — persistent list of every query you've asked, across sessions. Stored via `zodal-store-localstorage`. Rendering is schema-driven: column widths, sort, searchable fields all come from the `QueryRun` zod schema + `defineCollection(...)` affordances.

## Architecture

- **Backend** (`webapp/api/`) — FastAPI over the existing `semix` package.
  - `/api/typologies` — list WALS / Grambank / etc.
  - `/api/typologies/{name}/parameters` — list parameters
  - `/api/typologies/{name}/parameters/{id}/codes` — list possible values
  - `/api/typologies/{name}/languages/columns` — list metadata columns
  - `/api/query` — run a probabilistic query → `DistributionResult` or `ConditionalResult`
  - `/api/compare-estimators`, `/api/cross-validate`, `/api/rank-associations` — the secondary analyses
- **Frontend** (`webapp/ui/`) — Vite + React + TypeScript:
  - `src/lib/schemas.ts` — zod schemas mirroring the backend pydantic ones.
  - `src/lib/api.ts` — typed fetch client.
  - `src/stores/session.ts` — zustand slice for the current pending query.
  - `src/stores/historyCollection.ts` — **zodal** collection for persistent history.
  - `src/components/ui/` — shadcn-style primitives (button, card, command palette, popover, select, …).
  - `src/components/ParameterPicker.tsx` — searchable parameter combobox (cmdk).
  - `src/components/FilterChips.tsx` — chip-based filter builder with two kinds of conditions.
  - `src/components/EstimatorPicker.tsx` — preset-driven estimator selector.
  - `src/components/DistributionView.tsx` — bar-ranked distribution with click-to-drill rows.
  - `src/components/CPTView.tsx` — CPT heatmap with click-to-drill rows.
  - `src/components/ResultCard.tsx` — one query's result + its three secondary analyses.
  - `src/components/HistorySidebar.tsx` — zodal-backed persistent history panel.
  - `src/App.tsx` — three-pane shell.

## The zodal integration

Zodal's sweet spot in this app is the query history: a typed collection of
runtime-created records, persisted across reloads, with schema-driven list
rendering.

```ts
// src/stores/historyCollection.ts
export const QueryRunRecord = z.object({
  id: z.string(),
  created_at: z.string(),
  typology: z.string(),
  title: z.string(),
  target_id: z.string(),
  given_id: z.string().optional().default(""),
  kind: z.enum(["distribution", "conditional"]),
  estimator: z.string(),
  n_observations: z.number(),
  entropy_bits: z.number().optional().default(0),
  mutual_information_bits: z.number().optional().default(0),
  payload_json: z.string(),
});

export const queryRunCollection = defineCollection(QueryRunRecord, {
  idField: "id",
  labelField: "title",
  fields: {
    title: { searchable: true, columnWidth: 320 },
    created_at: { sortable: "desc", columnWidth: 160 },
    kind: { badge: { distribution: "secondary", conditional: "outline" } },
    payload_json: { storageRole: "content", visible: false, hidden: true },
    // …
  },
});

const provider = createLocalStorageProvider({
  storageKey: "semix.history.v1",
  idField: "id",
  searchFields: ["title", "target_id", "target_name", "typology", "given_id"],
});

export const useHistoryCollection = create(
  createZustandStoreSlice(queryRunCollection, provider),
);
```

The sidebar then calls `toColumnDefs(queryRunCollection)` — column config is
derived from the schema, not hand-written.

The parameter and code pickers (read-only data from the backend) don't
benefit from zodal's affordance layer — they're one-use comboboxes, so they
use TanStack Query + cmdk directly. That split (zodal for client-side typed
collections, direct React for ephemeral server projections) is deliberate.
