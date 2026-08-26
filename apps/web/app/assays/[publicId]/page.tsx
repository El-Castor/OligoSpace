import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { RecordDetails, RecordField } from "@/components/RecordDetails";
import { apiGetOptional, type AssaySummary, type ExperimentType, type OligoSummary, type PageResult, type TargetSummary } from "@/lib/api";
import { formatMetric } from "@/lib/registry-format";

export default async function AssayDetailPage({ params, searchParams }: { params: Promise<{ publicId: string }>; searchParams: Promise<{ updated?: string }> }) {
  const { publicId } = await params;
  const { updated } = await searchParams;
  const [assay, experimentTypes, oligoPage, targetPage] = await Promise.all([apiGetOptional<AssaySummary>(`/registry/assays/${encodeURIComponent(publicId)}`), apiGetOptional<ExperimentType[]>("/registry/experiment-types?active_only=false"), apiGetOptional<PageResult<OligoSummary>>("/registry/oligos?limit=200"), apiGetOptional<PageResult<TargetSummary>>("/registry/targets?limit=200")]);
  if (!assay) notFound();
  const method = experimentTypes?.find((item) => item.id === assay.experiment_type_id);
  const target = targetPage?.items.find((item) => item.id === assay.target_id);
  const oligos = new Map(oligoPage?.items.map((item) => [item.id, item]));
  return <><PageHeader eyebrow={`Assays / ${assay.public_id}`} title={assay.name} description="Reusable experimental design. Validation belongs to experiment evidence and is not inferred from this definition." action={<Link className="primary-button" href={`/assays/${assay.public_id}/edit`}>Edit assay</Link>} />{updated ? <div className="success-notice" role="status">Assay saved as version {assay.version}; the update was audited.</div> : null}<RecordDetails><RecordField label="Public ID">{assay.public_id}</RecordField><RecordField label="Status"><span className="badge">{assay.status}</span></RecordField><RecordField label="Method">{method?.name ?? "Unknown catalog entry"}</RecordField><RecordField label="Version">v{assay.version}</RecordField><RecordField label="Target">{target ? <Link className="text-link" href={`/targets/${target.public_id}`}>{target.public_id} · {target.name}</Link> : "Not specified"}</RecordField><RecordField label="Visibility">{assay.visibility}</RecordField><RecordField label="Expected amplicon">{formatMetric(assay.expected_amplicon_length, "bp")}</RecordField><RecordField label="Annealing temperature">{formatMetric(assay.recommended_annealing_temperature_c, "°C")}</RecordField><RecordField label="Expected product" wide>{assay.expected_product || "—"}</RecordField><RecordField label="Protocol notes" wide>{assay.protocol_notes || "—"}</RecordField></RecordDetails><section className="association-card"><h2>Oligos and roles</h2>{assay.oligos.length ? <div className="association-list">{assay.oligos.map((association) => { const oligo = oligos.get(association.oligo_id); return <div className="association-item" key={`${association.oligo_id}-${association.role}`}><span className="badge">{association.role.replaceAll("_", " ")}</span>{oligo ? <Link href={`/oligos/${oligo.public_id}`}><strong>{oligo.public_id}</strong> · {oligo.name}</Link> : <span>Inaccessible oligo</span>}{association.label ? <small>{association.label}</small> : null}</div>; })}</div> : <div className="empty"><strong>No oligos associated</strong>Add contextual oligo roles to make this assay reusable.</div>}</section></>;
}
