/**
 * Tag-chip UI for the two kinds of filters:
 *
 * - Language-metadata filters: column=value   (e.g. Family=Austronesian)
 * - Parameter-value filters:   parameter=code (e.g. 83A=83A-1)
 *
 * Chips are always visible above the query builder and in the result card's
 * title, so the user never loses track of what they're asking.
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, Plus, X } from "lucide-react";

import { listColumnValues, listLanguageColumns, listParameters } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CodePicker } from "./CodePicker";

type ConditionMap = Record<string, string | string[]>;

interface ChipsProps {
  typology: string;
  languageConditions: ConditionMap;
  parameterConditions: ConditionMap;
  onChange: (patch: {
    languageConditions?: ConditionMap;
    parameterConditions?: ConditionMap;
  }) => void;
}

export function FilterChips({
  typology,
  languageConditions,
  parameterConditions,
  onChange,
}: ChipsProps) {
  const removeLang = (col: string) => {
    const next = { ...languageConditions };
    delete next[col];
    onChange({ languageConditions: next });
  };
  const removeParam = (pid: string) => {
    const next = { ...parameterConditions };
    delete next[pid];
    onChange({ parameterConditions: next });
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {Object.entries(languageConditions).map(([col, val]) => (
        <Badge key={`L-${col}`} variant="secondary" className="gap-1">
          <span className="text-muted-foreground">{col}:</span>
          <span className="font-medium">{Array.isArray(val) ? val.join(" | ") : val}</span>
          <button
            onClick={() => removeLang(col)}
            className="ml-0.5 rounded-sm opacity-70 hover:opacity-100"
            aria-label="remove"
          >
            <X className="h-3 w-3" />
          </button>
        </Badge>
      ))}
      {Object.entries(parameterConditions).map(([pid, val]) => (
        <Badge key={`P-${pid}`} variant="secondary" className="gap-1">
          <span className="rounded bg-background/60 px-1 font-mono text-[10px] text-muted-foreground">
            {pid}
          </span>
          <span className="font-medium">=</span>
          <span className="font-medium">
            {Array.isArray(val) ? val.join(" | ") : val}
          </span>
          <button
            onClick={() => removeParam(pid)}
            className="ml-0.5 rounded-sm opacity-70 hover:opacity-100"
            aria-label="remove"
          >
            <X className="h-3 w-3" />
          </button>
        </Badge>
      ))}
      <AddConditionButton
        typology={typology}
        onAddLanguage={(col, v) =>
          onChange({ languageConditions: { ...languageConditions, [col]: v } })
        }
        onAddParameter={(pid, codeId) =>
          onChange({ parameterConditions: { ...parameterConditions, [pid]: codeId } })
        }
      />
    </div>
  );
}

function AddConditionButton({
  typology,
  onAddLanguage,
  onAddParameter,
}: {
  typology: string;
  onAddLanguage: (col: string, value: string) => void;
  onAddParameter: (parameterId: string, codeId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"root" | "lang-col" | "lang-val" | "param" | "param-val">(
    "root",
  );
  const [selectedCol, setSelectedCol] = useState<string | null>(null);
  const [selectedParam, setSelectedParam] = useState<string | null>(null);

  const reset = () => {
    setMode("root");
    setSelectedCol(null);
    setSelectedParam(null);
  };

  const langCols = useQuery({
    queryKey: ["lang-columns", typology],
    queryFn: () => listLanguageColumns(typology),
    enabled: open && (mode === "root" || mode === "lang-col"),
    staleTime: 1000 * 60 * 10,
  });

  const colValues = useQuery({
    queryKey: ["col-values", typology, selectedCol],
    queryFn: () => listColumnValues(typology, selectedCol!, 200),
    enabled: open && mode === "lang-val" && !!selectedCol,
    staleTime: 1000 * 60 * 10,
  });

  const parameters = useQuery({
    queryKey: ["parameters", typology],
    queryFn: () => listParameters(typology),
    enabled: open && (mode === "root" || mode === "param"),
    staleTime: 1000 * 60 * 10,
  });

  return (
    <Popover
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (!v) reset();
      }}
    >
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 gap-1 px-2 text-xs font-normal text-muted-foreground hover:text-foreground"
        >
          <Plus className="h-3 w-3" />
          Add condition
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[min(92vw,420px)] p-0" align="start">
        <Command>
          {mode === "root" && (
            <>
              <CommandInput placeholder="Filter by language property or parameter value…" />
              <CommandList>
                <CommandEmpty>No match.</CommandEmpty>
                <CommandGroup heading="Language property">
                  {(langCols.data || []).slice(0, 10).map((col) => (
                    <CommandItem
                      key={`col-${col.name}`}
                      value={col.name}
                      onSelect={() => {
                        setSelectedCol(col.name);
                        setMode("lang-val");
                      }}
                      className="items-start gap-2"
                    >
                      <span className="flex min-w-0 flex-1 flex-col">
                        <span className="font-medium">{col.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {col.sample_values.slice(0, 3).join(", ")}
                          {col.sample_values.length > 3 ? "…" : ""}
                        </span>
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {col.n_unique} values
                      </span>
                    </CommandItem>
                  ))}
                </CommandGroup>
                <CommandSeparator />
                <CommandGroup heading="Parameter value">
                  {(parameters.data || []).slice(0, 12).map((p) => (
                    <CommandItem
                      key={`p-${p.id}`}
                      value={`${p.id} ${p.name}`}
                      onSelect={() => {
                        setSelectedParam(p.id);
                        setMode("param-val");
                      }}
                      className="items-start gap-2"
                    >
                      <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                        {p.id}
                      </span>
                      <span className="flex-1 truncate font-medium">{p.name}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </>
          )}

          {mode === "lang-val" && selectedCol && (
            <>
              <div className="flex items-center justify-between border-b px-3 py-2 text-xs">
                <span className="text-muted-foreground">
                  Choose a value for <span className="font-medium text-foreground">{selectedCol}</span>
                </span>
                <button
                  className="rounded px-1.5 py-0.5 hover:bg-accent"
                  onClick={reset}
                >
                  ← back
                </button>
              </div>
              <CommandInput placeholder={`Search ${selectedCol}…`} />
              <CommandList>
                <CommandEmpty>No match.</CommandEmpty>
                <CommandGroup>
                  {(colValues.data || []).map((v) => (
                    <CommandItem
                      key={v}
                      value={v}
                      onSelect={() => {
                        onAddLanguage(selectedCol, v);
                        setOpen(false);
                        reset();
                      }}
                    >
                      <Check className={cn("mr-2 h-4 w-4 opacity-0")} />
                      {v}
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </>
          )}

          {mode === "param-val" && selectedParam && (
            <div className="p-3">
              <div className="mb-2 flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  Pick a value of{" "}
                  <span className="font-mono text-foreground">{selectedParam}</span>
                </span>
                <button
                  className="rounded px-1.5 py-0.5 hover:bg-accent"
                  onClick={reset}
                >
                  ← back
                </button>
              </div>
              <CodePicker
                typology={typology}
                parameterId={selectedParam}
                value={undefined}
                onChange={(codeId) => {
                  onAddParameter(selectedParam, codeId);
                  setOpen(false);
                  reset();
                }}
              />
            </div>
          )}
        </Command>
      </PopoverContent>
    </Popover>
  );
}
