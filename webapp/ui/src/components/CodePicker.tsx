/**
 * Picker for a single code (value) of a given parameter.
 *
 * Cheaper than ParameterPicker — each parameter has at most ~15 codes.
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown } from "lucide-react";

import { listCodes } from "@/lib/api";
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
  parameterId: string;
  value: string | undefined;
  onChange: (codeId: string) => void;
  placeholder?: string;
}

export function CodePicker({
  typology,
  parameterId,
  value,
  onChange,
  placeholder = "Pick a value…",
}: Props) {
  const [open, setOpen] = useState(false);
  const { data } = useQuery({
    queryKey: ["codes", typology, parameterId],
    queryFn: () => listCodes(typology, parameterId),
    enabled: !!parameterId,
    staleTime: 1000 * 60 * 10,
  });

  const current = (data || []).find((c) => c.id === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className="h-8 justify-between gap-2 font-normal"
          disabled={!parameterId}
        >
          <span className="truncate">
            {current ? (
              <span className="flex items-center gap-1.5">
                <span className="rounded bg-muted px-1 py-0.5 font-mono text-[10px]">
                  {current.id}
                </span>
                <span>{current.name || "—"}</span>
              </span>
            ) : (
              <span className="text-muted-foreground">{placeholder}</span>
            )}
          </span>
          <ChevronsUpDown className="h-4 w-4 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[min(92vw,360px)] p-0" align="start">
        <Command>
          <CommandInput placeholder="Search…" />
          <CommandList>
            <CommandEmpty>No code.</CommandEmpty>
            <CommandGroup>
              {(data || []).map((c) => (
                <CommandItem
                  key={c.id}
                  value={`${c.id} ${c.name}`}
                  onSelect={() => {
                    onChange(c.id);
                    setOpen(false);
                  }}
                  className="items-center gap-2"
                >
                  <Check
                    className={cn(
                      "h-4 w-4",
                      value === c.id ? "opacity-100" : "opacity-0",
                    )}
                  />
                  <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                    {c.id}
                  </span>
                  <span className="font-medium">{c.name || "—"}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
