/**
 * Examples strip — shown in the results pane when the history is empty.
 * Clicking an example populates the query builder and runs it.
 */
import { PlayCircle } from "lucide-react";
import type { QueryRequest } from "@/lib/schemas";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const EXAMPLES: { title: string; description: string; request: Omit<QueryRequest, "typology"> }[] = [
  {
    title: "P(subject–verb order)",
    description: "Global word-order distribution across all surveyed languages.",
    request: {
      target: "81A",
      condition: {},
      parameter_conditions: {},
      estimator: { name: "jeffreys", params: {} },
    },
  },
  {
    title: "P(word order | Austronesian)",
    description: "How Austronesian languages distribute over word orders.",
    request: {
      target: "81A",
      condition: { Family: "Austronesian" },
      parameter_conditions: {},
      estimator: { name: "laplace", params: { alpha: 0.5 } },
    },
  },
  {
    title: "P(word order | object–verb is OV)",
    description: "Classic drill: if objects precede verbs, subjects usually too.",
    request: {
      target: "81A",
      condition: {},
      parameter_conditions: { "83A": "83A-1" },
      estimator: { name: "laplace", params: { alpha: 0.5 } },
    },
  },
  {
    title: "P(object order | subject order)",
    description: "Full conditional probability table with mutual information.",
    request: {
      target: "83A",
      given: "81A",
      condition: {},
      parameter_conditions: {},
      estimator: { name: "laplace", params: { alpha: 0.5 } },
    },
  },
];

interface Props {
  typology: string;
  onPick: (req: QueryRequest) => void;
}

export function ExamplesStrip({ typology, onPick }: Props) {
  return (
    <div className="space-y-3">
      <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
        <PlayCircle className="h-4 w-4" />
        <span>Try one of these to get started</span>
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {EXAMPLES.map((ex) => (
          <Card
            key={ex.title}
            className="cursor-pointer transition-colors hover:bg-accent/40"
            onClick={() => onPick({ ...ex.request, typology })}
          >
            <CardContent className="p-4">
              <div className="font-medium">{ex.title}</div>
              <div className="mt-1 text-xs text-muted-foreground">{ex.description}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
