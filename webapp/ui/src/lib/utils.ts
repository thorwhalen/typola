import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a probability in compact form: 0.4092 → "0.409" / 0.00007 → "<0.001". */
export function fmtProb(p: number, precision = 3): string {
  if (!Number.isFinite(p)) return "–";
  if (p >= 0.995) return "≈1.000";
  if (p > 0 && p < 10 ** -precision) return `<${(10 ** -precision).toFixed(precision)}`;
  return p.toFixed(precision);
}

export function fmtBits(x: number, precision = 2): string {
  if (!Number.isFinite(x)) return "–";
  return `${x.toFixed(precision)} bits`;
}

export function fmtInt(x: number): string {
  return x.toLocaleString();
}
