/**
 * Searchable combobox for picking a parameter.
 *
 * Backed by TanStack Query against /api/typologies/{name}/parameters,
 * rendered with cmdk + shadcn Popover. The parameter list is ~200 items,
 * so we load it once and filter in-memory (cmdk's built-in fuzzy match).
 */
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown, X } from "lucide-react";

import { listParameters } from "@/lib/api";
import type { ParameterSummary } from "@/lib/schemas";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface Props {
  typology: string;
  value: string | undefined;
  onChange: (id: string | undefined) => void;
  placeholder?: string;
  allowClear?: boolean;
  className?: string;
}

export function ParameterPicker({
  typology,
  value,
  onChange,
  placeholder = "Pick a parameter…",
  allowClear = false,
  className,
}: Props) {
  const [open, setOpen] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ["parameters", typology],
    queryFn: () => listParameters(typology),
    staleTime: 1000 * 60 * 10,
  });

  const byId = useMemo(() => {
    const m = new Map<string, ParameterSummary>();
    (data || []).forEach((p) => m.set(p.id, p));
    return m;
  }, [data]);
  const current = value ? byId.get(value) : undefined;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn(
            "h-auto min-h-9 w-full justify-between gap-2 whitespace-normal text-left font-normal",
            className,
          )}
          disabled={isLoading}
        >
          <span className="flex min-w-0 flex-col">
            {current ? (
              <>
                <span className="flex items-center gap-1.5 font-medium">
                  <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                    {current.id}
                  </span>
                  <span className="truncate">{current.name}</span>
                </span>
              </>
            ) : (
              <span className="text-muted-foreground">
                {isLoading ? "Loading…" : placeholder}
              </span>
            )}
          </span>
          <span className="flex items-center gap-1">
            {allowClear && current && (
              <span
                role="button"
                tabIndex={-1}
                onClick={(e) => {
                  e.stopPropagation();
                  onChange(undefined);
                }}
                className="rounded p-0.5 opacity-50 hover:bg-accent hover:opacity-100"
              >
                <X className="h-3.5 w-3.5" />
              </span>
            )}
            <ChevronsUpDown className="h-4 w-4 shrink-0 opacity-50" />
          </span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[min(92vw,480px)] p-0" align="start">
        <Command>
          <CommandInput placeholder="Search by id or name…" />
          <CommandList>
            <CommandEmpty>No parameter matches.</CommandEmpty>
            <CommandGroup>
              {(data || []).map((p) => (
                <CommandItem
                  key={p.id}
                  value={`${p.id} ${p.name}`}
                  onSelect={() => {
                    onChange(p.id);
                    setOpen(false);
                  }}
                  className="items-start gap-2 py-2"
                >
                  <Check
                    className={cn(
                      "mt-0.5 h-4 w-4",
                      value === p.id ? "opacity-100" : "opacity-0",
                    )}
                  />
                  <span className="flex min-w-0 flex-1 flex-col">
                    <span className="flex items-center gap-1.5">
                      <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                        {p.id}
                      </span>
                      <span className="font-medium leading-tight">{p.name}</span>
                    </span>
                    <span className="mt-0.5 text-xs text-muted-foreground">
                      {p.n_codes} possible values
                    </span>
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
