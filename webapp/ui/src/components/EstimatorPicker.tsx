/**
 * Estimator picker.
 *
 * The main estimators don't need parameters (jeffreys, mle, uniform). For
 * laplace and empirical_bayes we expose a single numeric input so power-users
 * can tune it without cluttering the baseline. Everything else hides behind
 * a "…more" dropdown.
 */
import type { EstimatorSpec } from "@/lib/schemas";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Props {
  value: EstimatorSpec;
  onChange: (next: EstimatorSpec) => void;
}

const PRESETS: { label: string; description: string; spec: EstimatorSpec }[] = [
  {
    label: "Jeffreys",
    description: "Symmetric Dirichlet(α=0.5) — good default",
    spec: { name: "jeffreys", params: {} },
  },
  {
    label: "Laplace (α=1)",
    description: "Add-one smoothing",
    spec: { name: "laplace", params: { alpha: 1.0 } },
  },
  {
    label: "Laplace (α=0.5)",
    description: "Equivalent to Jeffreys",
    spec: { name: "laplace", params: { alpha: 0.5 } },
  },
  {
    label: "Laplace (α=0.1)",
    description: "Light smoothing",
    spec: { name: "laplace", params: { alpha: 0.1 } },
  },
  {
    label: "Empirical Bayes (strength=10)",
    description: "Shrink toward global mean",
    spec: { name: "empirical_bayes", params: { strength: 10.0 } },
  },
  {
    label: "MLE",
    description: "Raw frequencies; fails on unseen codes",
    spec: { name: "mle", params: {} },
  },
  {
    label: "Uniform",
    description: "Ignores counts",
    spec: { name: "uniform", params: {} },
  },
];

function labelFor(spec: EstimatorSpec): string {
  const preset = PRESETS.find(
    (p) =>
      p.spec.name === spec.name &&
      JSON.stringify(p.spec.params || {}) === JSON.stringify(spec.params || {}),
  );
  return preset?.label ?? `${spec.name}(${JSON.stringify(spec.params || {})})`;
}

export function EstimatorPicker({ value, onChange }: Props) {
  return (
    <Select
      value={labelFor(value)}
      onValueChange={(v) => {
        const preset = PRESETS.find((p) => p.label === v);
        if (preset) onChange(preset.spec);
      }}
    >
      <SelectTrigger className="h-9">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {PRESETS.map((p) => (
          <SelectItem key={p.label} value={p.label}>
            <span className="flex flex-col">
              <span className="font-medium">{p.label}</span>
              <span className="text-[10px] text-muted-foreground">{p.description}</span>
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export { PRESETS as ESTIMATOR_PRESETS };
