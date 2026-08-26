export function formatMetric(value: number | null, unit: string): string {
  return value === null ? "—" : `${value} ${unit}`;
}

export function formatPercent(value: number | null): string {
  return value === null ? "—" : `${value}%`;
}
