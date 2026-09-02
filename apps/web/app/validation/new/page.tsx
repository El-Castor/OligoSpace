import { createValidation } from "@/app/validation/actions";
import { PageHeader } from "@/components/PageHeader";
import { ValidationForm } from "@/components/ValidationForm";
import { apiGetOptional, type AssaySummary, type ExperimentRunSummary, type ExperimentType, type PageResult, type ValidationSummary } from "@/lib/api";

export default async function NewValidationPage({ searchParams }: { searchParams: Promise<{ assay?: string; run?: string; supersedes?: string; error?: string }> }) {
  const state = await searchParams;
  const [assayPage, runPage, experimentTypes, superseded] = await Promise.all([apiGetOptional<PageResult<AssaySummary>>("/registry/assays?limit=200"), apiGetOptional<PageResult<ExperimentRunSummary>>("/laboratory/runs?limit=200"), apiGetOptional<ExperimentType[]>("/registry/experiment-types?active_only=false"), state.supersedes ? apiGetOptional<ValidationSummary>(`/laboratory/validations/${encodeURIComponent(state.supersedes)}`) : Promise.resolve(null)]);
  const assays = assayPage?.items ?? [];
  const runs = runPage?.items ?? [];
  const selectedRun = runs.find((run) => run.public_id === state.run);
  const selectedAssay = assays.find((assay) => assay.public_id === state.assay) ?? assays.find((assay) => assay.id === selectedRun?.assay_id);
  return <><PageHeader eyebrow="Lab / validation" title="Record contextual validation" description="Append a dated conclusion and method-specific measurements to an assay or one of its runs. This never validates an oligo globally." /><ValidationForm action={createValidation} assays={assays} runs={runs.filter((run) => !selectedAssay || run.assay_id === selectedAssay.id)} experimentTypes={experimentTypes ?? []} assayId={selectedAssay?.id} runId={selectedRun?.id} supersedes={superseded ?? undefined} error={state.error} /></>;
}
