import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { RecordDetails, RecordField } from "@/components/RecordDetails";
import { apiGetOptional, type Organism, type TargetSummary } from "@/lib/api";

export default async function TargetDetailPage({ params, searchParams }: { params: Promise<{ publicId: string }>; searchParams: Promise<{ updated?: string }> }) {
  const { publicId } = await params;
  const { updated } = await searchParams;
  const [target, organisms] = await Promise.all([apiGetOptional<TargetSummary>(`/registry/targets/${encodeURIComponent(publicId)}`), apiGetOptional<Organism[]>("/registry/organisms")]);
  if (!target) notFound();
  const organism = organisms?.find((item) => item.id === target.organism_id);
  return <><PageHeader eyebrow={`Targets / ${target.public_id}`} title={target.name} description="Declared biological target. Exact mapping facts require a governed reference and a provenance-bearing analysis." action={<Link className="primary-button" href={`/targets/${target.public_id}/edit`}>Edit target</Link>} />{updated ? <div className="success-notice" role="status">Target updated and audited.</div> : null}<RecordDetails><RecordField label="Public ID">{target.public_id}</RecordField><RecordField label="Status"><span className="badge">{target.status}</span></RecordField><RecordField label="Type">{target.target_type}</RecordField><RecordField label="Visibility">{target.visibility}</RecordField><RecordField label="Organism">{organism?.scientific_name ?? "Not specified"}</RecordField><RecordField label="Gene identifier">{target.gene_identifier || "—"}</RecordField><RecordField label="Transcript identifier">{target.transcript_identifier || "—"}</RecordField><RecordField label="Description" wide>{target.description || "—"}</RecordField><RecordField label="Reference sequence" wide>{target.reference_sequence ? <span className="sequence sequence-block">{target.reference_sequence}</span> : "Not supplied"}</RecordField></RecordDetails></>;
}
