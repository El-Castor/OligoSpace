import { createExperimentRun } from "@/app/experiments/actions";
import { ExperimentRunForm } from "@/components/ExperimentRunForm";
import { PageHeader } from "@/components/PageHeader";
import { apiGet, apiGetOptional, type AssaySummary, type PageResult, type WorkspaceChoices } from "@/lib/api";

export default async function NewExperimentRunPage({ searchParams }: { searchParams: Promise<{ assay?: string; error?: string }> }) {
  const { assay: assayPublicId, error } = await searchParams;
  const [assayPage, choices] = await Promise.all([apiGetOptional<PageResult<AssaySummary>>("/registry/assays?limit=200"), apiGet<WorkspaceChoices>("/workspace/choices")]);
  const assays = assayPage?.items ?? [];
  const assayId = assays.find((item) => item.public_id === assayPublicId)?.id;
  return <><PageHeader eyebrow="Research / experiment runs" title="Record an experiment run" description="Capture one execution of a reusable assay with its exact version, operator, timestamp, conditions, inputs, and protocol provenance." />{!assayPage ? <div className="notice">Assay catalogue unavailable.</div> : null}<ExperimentRunForm action={createExperimentRun} assays={assays} choices={choices} assayId={assayId} error={error} /></>;
}
