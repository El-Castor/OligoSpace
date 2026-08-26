import { PageHeader } from "@/components/PageHeader";
import { RegistryTable } from "@/components/RegistryTable";
import { apiGetOptional, type OligoSummary, type PageResult } from "@/lib/api";
import { formatMetric, formatPercent } from "@/lib/registry-format";

export default async function OligosPage() {
  const result = await apiGetOptional<PageResult<OligoSummary>>("/registry/oligos");
  const items = result?.items ?? [];
  return (
    <>
      <PageHeader eyebrow="Research / registry" title="Oligos" description="Biological sequence identities, calculated properties, provenance, and reuse—separate from tubes and assay roles." action={<button className="primary-button" type="button" disabled title="Create workflow is the next registry increment">New oligo</button>} />
      {!result ? <div className="notice">API unavailable. The table is empty rather than populated with fictional records.</div> : null}
      <RegistryTable count={result?.total ?? 0} columns={["ID", "Name", "Sequence 5′→3′", "Length", "GC", "Tm", "Status"]}>
        {items.map((oligo) => <tr key={oligo.id}><td className="public-id">{oligo.public_id}</td><td>{oligo.name}</td><td className="sequence">{oligo.normalized_sequence}</td><td>{formatMetric(oligo.sequence_length, "nt")}</td><td>{formatPercent(oligo.gc_percent)}</td><td>{formatMetric(oligo.melting_temperature_c, "°C")}</td><td><span className="badge">{oligo.status}</span></td></tr>)}
      </RegistryTable>
    </>
  );
}
