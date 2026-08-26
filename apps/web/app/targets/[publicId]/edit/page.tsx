import { notFound } from "next/navigation";

import { updateTarget } from "@/app/targets/actions";
import { PageHeader } from "@/components/PageHeader";
import { TargetForm } from "@/components/TargetForm";
import { apiGetOptional, type Organism, type TargetSummary } from "@/lib/api";

export default async function EditTargetPage({ params, searchParams }: { params: Promise<{ publicId: string }>; searchParams: Promise<{ error?: string }> }) {
  const { publicId } = await params;
  const { error } = await searchParams;
  const [target, organisms] = await Promise.all([apiGetOptional<TargetSummary>(`/registry/targets/${encodeURIComponent(publicId)}`), apiGetOptional<Organism[]>("/registry/organisms")]);
  if (!target) notFound();
  return <><PageHeader eyebrow={`Targets / ${target.public_id}`} title="Edit target" description="Changes are authorized by the API and recorded in the audit trail." /><TargetForm action={updateTarget.bind(null, target.public_id)} target={target} organisms={organisms ?? []} error={error} /></>;
}
