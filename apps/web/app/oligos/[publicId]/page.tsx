import Link from "next/link";
import { notFound } from "next/navigation";

import { runOligoPrimer3 } from "@/app/scientific-jobs/actions";
import { PageHeader } from "@/components/PageHeader";
import { Primer3JobSection } from "@/components/Primer3JobSection";
import { RecordDetails, RecordField } from "@/components/RecordDetails";
import {
  apiGetOptional,
  apiGet,
  type CurrentUser,
  type OligoSummary,
  type PageResult,
  type ScientificJobSummary,
} from "@/lib/api";
import { formatMetric, formatPercent } from "@/lib/registry-format";

export default async function OligoDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ publicId: string }>;
  searchParams: Promise<{
    updated?: string;
    warning?: string;
    scientific_job?: string;
    scientific_error?: string;
  }>;
}) {
  const { publicId } = await params;
  const state = await searchParams;
  const [oligo, user] = await Promise.all([
    apiGetOptional<OligoSummary>(`/registry/oligos/${encodeURIComponent(publicId)}`),
    apiGet<CurrentUser>("/me"),
  ]);
  if (!oligo) notFound();
  const jobPage = await apiGetOptional<PageResult<ScientificJobSummary>>(
    `/scientific-jobs?oligo_id=${encodeURIComponent(oligo.id)}&limit=50`,
  );
  const action = runOligoPrimer3.bind(null, oligo.public_id);
  return (
    <>
      <PageHeader
        eyebrow={`Oligos / ${oligo.public_id}`}
        title={oligo.name}
        description="Biological identity and calculated sequence facts. Assay direction and physical stock remain separate records."
        action={
          <Link className="primary-button" href={`/oligos/${oligo.public_id}/edit`}>
            Edit metadata
          </Link>
        }
      />
      {state.updated ? <div className="success-notice" role="status">Oligo metadata updated and audited.</div> : null}
      {state.warning ? <div className="notice" role="status">A reverse-complement match already exists. Review both records before reuse.</div> : null}
      {state.scientific_job ? <div className="success-notice" role="status">Scientific job {state.scientific_job} was persisted and queued.</div> : null}
      {state.scientific_error ? <div className="notice" role="alert">{state.scientific_error}</div> : null}
      <RecordDetails>
        <RecordField label="Public ID">{oligo.public_id}</RecordField>
        <RecordField label="Status"><span className="badge">{oligo.status}</span></RecordField>
        <RecordField label="Type">{oligo.oligo_type}</RecordField>
        <RecordField label="Visibility">{oligo.visibility}</RecordField>
        <RecordField label="Length">{formatMetric(oligo.sequence_length, "nt")}</RecordField>
        <RecordField label="GC">{formatPercent(oligo.gc_percent)}</RecordField>
        <RecordField label="Wallace screening Tm">{formatMetric(oligo.melting_temperature_c, "°C")}</RecordField>
        <RecordField label="Molecular weight">{formatMetric(oligo.molecular_weight_g_mol, "g/mol")}</RecordField>
        <RecordField label="Sequence 5′→3′" wide><span className="sequence sequence-block">{oligo.normalized_sequence}</span></RecordField>
        <RecordField label="Reverse complement" wide><span className="sequence sequence-block">{oligo.reverse_complement}</span></RecordField>
        <RecordField label="Description" wide>{oligo.description || "—"}</RecordField>
        <RecordField label="Notes" wide>{oligo.notes || "—"}</RecordField>
      </RecordDetails>
      <section className="provenance-card">
        <h2>Wallace screening provenance</h2>
        <p>This synchronous approximation is a screening fact, not a Primer3 nearest-neighbor result or experimental validation.</p>
        <pre>{JSON.stringify(oligo.calculation_provenance, null, 2)}</pre>
      </section>
      <Primer3JobSection
        title="Scientific QC"
        description={`Primer3 analysis of ${oligo.public_id} using its immutable 5′→3′ sequence snapshot.`}
        action={user.role === "viewer" ? undefined : action}
        jobs={jobPage?.items ?? []}
      />
    </>
  );
}
