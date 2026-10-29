import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { RecordDetails, RecordField } from "@/components/RecordDetails";
import { apiGetOptional, type OligoSummary } from "@/lib/api";
import { formatMetric, formatPercent } from "@/lib/registry-format";

export default async function OligoDetailPage({ params, searchParams }: { params: Promise<{ publicId: string }>; searchParams: Promise<{ updated?: string; warning?: string }> }) {
  const { publicId } = await params;
  const state = await searchParams;
  const oligo = await apiGetOptional<OligoSummary>(`/registry/oligos/${encodeURIComponent(publicId)}`);
  if (!oligo) notFound();
  return <><PageHeader eyebrow={`Oligos / ${oligo.public_id}`} title={oligo.name} description="Biological identity and calculated sequence facts. Assay direction and physical stock remain separate records." action={<Link className="primary-button" href={`/oligos/${oligo.public_id}/edit`}>Edit metadata</Link>} />{state.updated ? <div className="success-notice" role="status">Oligo metadata updated and audited.</div> : null}{state.warning ? <div className="notice" role="status">A reverse-complement match already exists. Review both records before reuse.</div> : null}<RecordDetails><RecordField label="Public ID">{oligo.public_id}</RecordField><RecordField label="Status"><span className="badge">{oligo.status}</span></RecordField><RecordField label="Type">{oligo.oligo_type}</RecordField><RecordField label="Visibility">{oligo.visibility}</RecordField><RecordField label="Length">{formatMetric(oligo.sequence_length, "nt")}</RecordField><RecordField label="GC">{formatPercent(oligo.gc_percent)}</RecordField><RecordField label="Screening Tm">{formatMetric(oligo.melting_temperature_c, "°C")}</RecordField><RecordField label="Molecular weight">{formatMetric(oligo.molecular_weight_g_mol, "g/mol")}</RecordField><RecordField label="Sequence 5′→3′" wide><span className="sequence sequence-block">{oligo.normalized_sequence}</span></RecordField><RecordField label="Reverse complement" wide><span className="sequence sequence-block">{oligo.reverse_complement}</span></RecordField><RecordField label="Description" wide>{oligo.description || "—"}</RecordField><RecordField label="Notes" wide>{oligo.notes || "—"}</RecordField></RecordDetails><section className="provenance-card"><h2>Calculation provenance</h2><p>These are calculated screening facts, not experimental validation.</p><pre>{JSON.stringify(oligo.calculation_provenance, null, 2)}</pre></section></>;
}
