import Link from "next/link";

import { registryData } from "@/lib/registry-data";
import { registryOffset } from "@/lib/registry-page";
import { ScientificValue } from "@/components/ScientificValue";
import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { RegistryTable } from "@/components/RegistryTable";
import { type OligoSummary, type PageResult } from "@/lib/api";
import { formatMetric, formatPercent } from "@/lib/registry-format";

export default async function OligosPage({ searchParams }: { searchParams: Promise<{ q?: string; offset?: string }> }) {
  const params = await searchParams;
  const query = params.q?.trim() ?? "";
  const offset = registryOffset(params.offset);
  const { result, error } = await registryData<PageResult<OligoSummary>>(`/registry/oligos?q=${encodeURIComponent(query)}&offset=${offset}`);
  const items = result?.items ?? [];
  return (
    <>
      <PageHeader eyebrow="Research / registry" title="Oligos" description="Biological sequence identities, calculated properties, provenance, and reuse—separate from tubes and assay roles." action={<Link className="primary-button" href="/oligos/new">New oligo</Link>} />
      <RegistrySearch action="/oligos" query={query} />
      <a className="secondary-button" href={`/oligos/export?q=${encodeURIComponent(query)}`}>Export visible oligos (CSV)</a>
      <RegistryTable shown={items.length} label="Oligos" query={query} path="/oligos" offset={result?.offset ?? offset} limit={result?.limit ?? 50} error={error} count={result?.total ?? 0} columns={["ID", "Name", "Sequence 5′→3′", "Length", "GC", "Tm", "Status"]}>
        {items.map((oligo) => <tr key={oligo.id}><td className="public-id"><ScientificValue value={oligo.public_id} href={`/oligos/${oligo.public_id}`} copy /></td><td><ScientificValue value={oligo.name} href={`/oligos/${oligo.public_id}`} /></td><td><ScientificValue value={oligo.normalized_sequence} sequence copy /></td><td className="numeric">{formatMetric(oligo.sequence_length, "nt")}</td><td className="numeric">{formatPercent(oligo.gc_percent)}</td><td className="numeric">{formatMetric(oligo.melting_temperature_c, "°C")}</td><td><span className="badge">{oligo.status}</span></td></tr>)}
      </RegistryTable>
    </>
  );
}
