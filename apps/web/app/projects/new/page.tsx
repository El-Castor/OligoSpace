import { createProject } from "@/app/workspace/actions";
import { PageHeader } from "@/components/PageHeader";
import { ProjectForm } from "@/components/ProjectForm";
import { apiGet, type TeamSummary } from "@/lib/api";

export default async function NewProjectPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  const teams = await apiGet<TeamSummary[]>("/workspace/teams");
  return <><PageHeader eyebrow="Workspace / projects" title="Create a project" description="The creator becomes project owner. Membership and visibility are enforced by the API." /><ProjectForm action={createProject} teams={teams} error={error} /></>;
}
