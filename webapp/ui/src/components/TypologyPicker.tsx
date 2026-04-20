/**
 * Top-bar typology picker. Shows licence and observation counts.
 */
import { useQuery } from "@tanstack/react-query";
import { Database, Scale } from "lucide-react";

import { listTypologies } from "@/lib/api";
import { cn, fmtInt } from "@/lib/utils";
import { useSession } from "@/stores/session";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function TypologyPicker() {
  const { typology, setTypology } = useSession();
  const { data } = useQuery({
    queryKey: ["typologies"],
    queryFn: listTypologies,
    staleTime: Infinity,
  });
  const current = data?.find((t) => t.name === typology);

  return (
    <div className="flex items-center gap-3">
      <Select value={typology} onValueChange={setTypology}>
        <SelectTrigger className="h-8 w-36">
          <Database className="mr-1.5 h-3.5 w-3.5 text-muted-foreground" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {(data || []).map((t) => (
            <SelectItem key={t.name} value={t.name}>
              <span className="flex flex-col">
                <span className="font-medium capitalize">{t.name}</span>
                <span className="text-[10px] text-muted-foreground">
                  {fmtInt(t.n_languages)} langs · {t.n_parameters} params
                </span>
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {current && (
        <div className="hidden items-center gap-2 text-xs text-muted-foreground md:flex">
          <span>
            {fmtInt(current.n_languages)} languages · {current.n_parameters} parameters ·{" "}
            {fmtInt(current.n_values)} observations
          </span>
          {current.license && (
            <Badge variant="outline" className="gap-1 text-[10px]">
              <Scale className="h-3 w-3" />
              {current.license}
            </Badge>
          )}
        </div>
      )}
    </div>
  );
}
