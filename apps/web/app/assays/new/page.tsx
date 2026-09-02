import { createAssay } from "@/app/assays/actions";
import { AssayForm } from "@/components/AssayForm";
import { PageHeader } from "@/components/PageHeader";
import { apiGet, apiGetOptional, type ExperimentType, type OligoSummary, type PageResult, type TargetSummary, type WorkspaceChoices } from "@/lib/api";

export default async function NewAssayPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  const [experimentTypes, oligoPage, targetPage] = await Promise.all([apiGetOptional<ExperimentType[]>("/registry/experiment-types"), apiGetOptional<PageResult<OligoSummary>>("/registry/oligos?limit=200"), apiGetOptional<PageResult<TargetSummary>>("/registry/targets?limit=200")]);
  const choices = await apiGet<WorkspaceChoices>("/workspace/choices");
  const unavailable = !experimentTypes || !oligoPage || !targetPage;
  return <><PageHeader eyebrow="Research / assays" title="Register an assay" description="Combine reusable oligo identities with contextual roles, a method, and an optional biological target." />{unavailable ? <div className="notice">One or more catalogs are unavailable. Start the full stack before registering an assay.</div> : null}<AssayForm action={createAssay} experimentTypes={experimentTypes ?? []} oligos={oligoPage?.items ?? []} targets={targetPage?.items ?? []} choices={choices} error={error} /></>;
}
