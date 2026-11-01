import type { ReactNode } from "react";
import Link from "next/link";
import { ScientificTableFrame } from "@/components/ScientificTableFrame";
import { registryHref } from "@/lib/registry-page";

export function RegistryTable({
  count,
  columns,
  children,
  label = "Registry", query = "", path, limit = 50, offset = 0, error, shown,
}: {
  count: number;
  columns: string[];
  children: ReactNode;
  label?: string; query?: string; path?: string; limit?: number; offset?: number; error?: string; shown?: number;
}) {
  return (
    <ScientificTableFrame label={label} summary={error ? "Records unavailable" : `${count} records visible${path && count && shown !== 0 ? ` · ${Math.min(offset + 1, count)}–${Math.min(offset + limit, count)} shown` : ""}`}>
      {error ? <div className="notice table-state" role="alert">{error}</div> : count && shown === 0 ? <div className="empty"><strong>No records on this page</strong>{path ? <Link href={registryHref(path, query, 0)}>Return to first page</Link> : null}</div> : count ? (
        <table aria-label={label}>
          <thead><tr>{columns.map((column) => <th scope="col" className={["Length", "GC", "Tm", "Expected amplicon", "Version"].includes(column) ? "numeric" : undefined} key={column}>{column}</th>)}</tr></thead>
          <tbody>{children}</tbody>
        </table>
      ) : (
        <div className="empty"><strong>{query ? "No matching records" : "No records yet"}</strong>{query ? "Try another search or clear the active query." : "No records are currently visible in this registry."}</div>
      )}
      {!error && path && count > limit ? <nav className="table-pagination" aria-label={`${label} pages`}>
        {offset > 0 ? <Link href={registryHref(path, query, Math.max(0, offset - limit))}>Previous page</Link> : <span>First page</span>}
        {offset + limit < count ? <Link href={registryHref(path, query, offset + limit)}>Next page</Link> : <span>Last page</span>}
      </nav> : null}
    </ScientificTableFrame>
  );
}
