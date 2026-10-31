import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { RegistryTable } from "@/components/RegistryTable";
import { ScientificValue } from "@/components/ScientificValue";
import { RegistrySearch } from "@/components/RegistrySearch";
import { registryData } from "@/lib/registry-data";
import { type ProjectSummary } from "@/lib/api";

export default async function ProjectsPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q = "" } = await searchParams;
  const { result, error } = await registryData<ProjectSummary[]>(`/workspace/projects${q ? `?q=${encodeURIComponent(q)}` : ""}`);
  const projects = result ?? [];
  return (
    <>
      <PageHeader eyebrow="Workspace" title="Projects" description="Stable collaborative workspaces with explicit members, visibility, linked oligos, and linked assays." action={<Link className="primary-button" href="/projects/new">Create project</Link>} />
      <RegistrySearch action="/projects" query={q} />
      <RegistryTable error={error} label="Projects" query={q} count={projects.length} columns={["ID", "Name", "Team", "Visibility", "Resources", "Status"]}>
            {projects.map((project) => <tr key={project.id}><td className="public-id"><ScientificValue value={project.public_id} href={`/projects/${project.public_id}`} copy /></td><td><ScientificValue value={project.name} href={`/projects/${project.public_id}`} /><small className="table-subline">Owner: {project.owner_name}</small></td><td>{project.team_name ?? "—"}</td><td><span className="badge">{project.visibility === "organization" ? "Institute" : project.visibility}</span></td><td>{project.oligo_count} oligos · {project.assay_count} assays</td><td><span className="badge">{project.status}</span></td></tr>)}
      </RegistryTable>
    </>
  );
}
