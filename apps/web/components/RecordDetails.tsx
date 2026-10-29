import type { ReactNode } from "react";

export function RecordDetails({ children }: { children: ReactNode }) {
  return <dl className="record-details">{children}</dl>;
}

export function RecordField({ label, children, wide = false }: { label: string; children: ReactNode; wide?: boolean }) {
  return <div className={wide ? "record-field record-field-wide" : "record-field"}><dt>{label}</dt><dd>{children ?? "—"}</dd></div>;
}
