import { notFound } from "next/navigation";

import { updateProject } from "@/app/workspace/actions";
import { PageHeader } from "@/components/PageHeader";
import { ProjectForm } from "@/components/ProjectForm";
import { apiGetOptional, type ProjectSummary, type TeamSummary } from "@/lib/api";

export default async function EditProjectPage({ params, searchParams }: { params: Promise<{ publicId: string }>; searchParams: Promise<{ error?: string }> }) {
  const { publicId } = await params;
  const { error } = await searchParams;
  const [project, teams] = await Promise.all([apiGetOptional<ProjectSummary>(`/workspace/projects/${encodeURIComponent(publicId)}`), apiGetOptional<TeamSummary[]>("/workspace/teams")]);
  if (!project) notFound();
  return <><PageHeader eyebrow={`Projects / ${project.public_id}`} title="Edit project" description="Status, team association, and visibility changes are authorized and audited." /><ProjectForm action={updateProject.bind(null, project.public_id)} teams={teams ?? []} project={project} error={error} /></>;
}
