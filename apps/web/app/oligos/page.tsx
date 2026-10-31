import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { RegistryTable } from "@/components/RegistryTable";
import { apiGetOptional, type OligoSummary, type PageResult } from "@/lib/api";
import { formatMetric, formatPercent } from "@/lib/registry-format";

export default async function OligosPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const query = (await searchParams).q?.trim() ?? "";
  const result = await apiGetOptional<PageResult<OligoSummary>>(`/registry/oligos${query ? `?q=${encodeURIComponent(query)}` : ""}`);
  const items = result?.items ?? [];
  return (
    <>
      <PageHeader eyebrow="Research / registry" title="Oligos" description="Biological sequence identities, calculated properties, provenance, and reuse—separate from tubes and assay roles." action={<Link className="primary-button" href="/oligos/new">New oligo</Link>} />
      <RegistrySearch action="/oligos" query={query} />
      <a className="secondary-button" href={`/oligos/export?q=${encodeURIComponent(query)}`}>Export visible oligos (CSV)</a>
      {!result ? <div className="notice">API unavailable. The table is empty rather than populated with fictional records.</div> : null}
      <RegistryTable count={result?.total ?? 0} columns={["ID", "Name", "Sequence 5′→3′", "Length", "GC", "Tm", "Status"]}>
        {items.map((oligo) => <tr key={oligo.id}><td className="public-id"><Link href={`/oligos/${oligo.public_id}`}>{oligo.public_id}</Link></td><td><Link className="row-link" href={`/oligos/${oligo.public_id}`}>{oligo.name}</Link></td><td className="sequence">{oligo.normalized_sequence}</td><td>{formatMetric(oligo.sequence_length, "nt")}</td><td>{formatPercent(oligo.gc_percent)}</td><td>{formatMetric(oligo.melting_temperature_c, "°C")}</td><td><span className="badge">{oligo.status}</span></td></tr>)}
      </RegistryTable>
    </>
  );
}
