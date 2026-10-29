import { notFound } from "next/navigation";

import { updateAssay } from "@/app/assays/actions";
import { AssayForm } from "@/components/AssayForm";
import { PageHeader } from "@/components/PageHeader";
import { apiGet, apiGetOptional, type AssaySummary, type ExperimentType, type OligoSummary, type PageResult, type TargetSummary, type WorkspaceChoices } from "@/lib/api";

export default async function EditAssayPage({ params, searchParams }: { params: Promise<{ publicId: string }>; searchParams: Promise<{ error?: string }> }) {
  const { publicId } = await params;
  const { error } = await searchParams;
  const [assay, experimentTypes, oligoPage, targetPage] = await Promise.all([apiGetOptional<AssaySummary>(`/registry/assays/${encodeURIComponent(publicId)}`), apiGetOptional<ExperimentType[]>("/registry/experiment-types"), apiGetOptional<PageResult<OligoSummary>>("/registry/oligos?limit=200"), apiGetOptional<PageResult<TargetSummary>>("/registry/targets?limit=200")]);
  if (!assay) notFound();
  const choices = await apiGet<WorkspaceChoices>("/workspace/choices");
  return <><PageHeader eyebrow={`Assays / ${assay.public_id}`} title={`Edit assay v${assay.version}`} description="Saving increments the assay version and records before/after audit evidence." /><AssayForm action={updateAssay.bind(null, assay.public_id)} assay={assay} experimentTypes={experimentTypes ?? []} oligos={oligoPage?.items ?? []} targets={targetPage?.items ?? []} choices={choices} error={error} /></>;
}
