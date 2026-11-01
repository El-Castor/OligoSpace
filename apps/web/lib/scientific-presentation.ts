const descriptions: Record<string, string> = {
  queued: "Queued by the server. No result is confirmed yet.",
  running: "Execution is running. Results are not confirmed until persisted.",
  retrying: "The server has scheduled another attempt. No result is confirmed yet.",
  succeeded: "Execution completed. Review the persisted results and their provenance.",
  failed: "Execution failed. Review the recorded error and attempts; no successful result is implied.",
};

export function jobStateDescription(state: string): string {
  return descriptions[state] ?? `Server-reported state: ${state}.`;
}

export function scientificObject(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

export function jobInputSequences(snapshot: Record<string, unknown>): Array<{ label: string; sequence: string; publicId?: string }> {
  const subject = scientificObject(snapshot.subject);
  const sequence = scientificObject(snapshot.sequence);
  if (subject?.type === "oligo" && typeof sequence?.normalized === "string") {
    return [{ label: "Oligo input · 5′→3′", sequence: sequence.normalized, publicId: typeof subject.public_id === "string" ? subject.public_id : undefined }];
  }
  return (["forward", "reverse"] as const).flatMap((role) => {
    const input = scientificObject(snapshot[role]);
    return typeof input?.normalized_sequence === "string" ? [{ label: `${role === "forward" ? "Forward" : "Reverse"} input · 5′→3′`, sequence: input.normalized_sequence, publicId: typeof input.public_id === "string" ? input.public_id : undefined }] : [];
  });
}

export function jobSourceHref(snapshot: Record<string, unknown>): string | undefined {
  const subject = scientificObject(snapshot.subject);
  if (typeof subject?.public_id !== "string") return undefined;
  if (subject.type === "oligo") return `/oligos/${encodeURIComponent(subject.public_id)}`;
  if (subject.type === "assay") return `/assays/${encodeURIComponent(subject.public_id)}`;
  return undefined;
}
