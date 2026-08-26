import { notFound } from "next/navigation";

import { updateOligo } from "@/app/oligos/actions";
import { OligoForm } from "@/components/OligoForm";
import { PageHeader } from "@/components/PageHeader";
import { apiGetOptional, type OligoSummary } from "@/lib/api";

export default async function EditOligoPage({ params, searchParams }: { params: Promise<{ publicId: string }>; searchParams: Promise<{ error?: string }> }) {
  const { publicId } = await params;
  const { error } = await searchParams;
  const oligo = await apiGetOptional<OligoSummary>(`/registry/oligos/${encodeURIComponent(publicId)}`);
  if (!oligo) notFound();
  return <><PageHeader eyebrow={`Oligos / ${oligo.public_id}`} title="Edit oligo metadata" description="The biological sequence is intentionally immutable. This change will create an audit event." /><OligoForm action={updateOligo.bind(null, oligo.public_id)} oligo={oligo} error={error} /></>;
}
