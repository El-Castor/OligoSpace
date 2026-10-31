"use client";

import { useId, useState, type ReactNode } from "react";

export function ScientificTableFrame({ label, summary, children }: { label: string; summary: string; children: ReactNode }) {
  const [compact, setCompact] = useState(false);
  const id = useId();
  return <section className="table-card scientific-table" data-density={compact ? "compact" : "comfortable"} aria-label={label}>
    <div className="table-tools"><span id={id}>{summary}</span><div className="density-control" role="group" aria-label="Table density">
      <button type="button" aria-pressed={!compact} onClick={() => setCompact(false)}>Comfortable</button>
      <button type="button" aria-pressed={compact} onClick={() => setCompact(true)}>Compact</button>
    </div></div>
    <div className="table-scroll" role="region" aria-label={`${label} data`} aria-describedby={id} tabIndex={0}>{children}</div>
  </section>;
}
