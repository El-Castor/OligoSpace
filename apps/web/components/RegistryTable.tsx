import type { ReactNode } from "react";

export function RegistryTable({
  count,
  columns,
  children,
}: {
  count: number;
  columns: string[];
  children: ReactNode;
}) {
  return (
    <div className="table-card">
      <div className="table-tools"><span>{count} records visible</span><span>Filters · Columns</span></div>
      {count ? (
        <table>
          <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
          <tbody>{children}</tbody>
        </table>
      ) : (
        <div className="empty"><strong>No records yet</strong>The registry is ready for its first reviewed entry.</div>
      )}
    </div>
  );
}
