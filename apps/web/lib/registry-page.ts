export function registryOffset(value?: string): number {
  if (!value || !/^\d+$/.test(value)) return 0;
  const offset = Number(value);
  return Number.isSafeInteger(offset) ? offset : 0;
}

export function registryHref(path: string, query: string, offset: number): string {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  if (offset) params.set("offset", String(offset));
  return `${path}${params.size ? `?${params}` : ""}`;
}

export function registryFailure(status?: number): string {
  if (status === 403) return "Access denied. Your current permissions do not allow this list.";
  if (status === 401) return "Session required. Sign in again to load this list.";
  return "Records could not be loaded. Retry this page; no empty result is assumed.";
}
