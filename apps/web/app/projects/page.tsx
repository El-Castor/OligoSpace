import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { apiGet, type ProjectSummary } from "@/lib/api";

export default async function ProjectsPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q = "" } = await searchParams;
  const projects = await apiGet<ProjectSummary[]>(`/workspace/projects${q ? `?q=${encodeURIComponent(q)}` : ""}`);
  return (
    <>
      <PageHeader eyebrow="Workspace" title="Projects" description="Stable collaborative workspaces with explicit members, visibility, linked oligos, and linked assays." action={<Link className="primary-button" href="/projects/new">Create project</Link>} />
      <RegistrySearch action="/projects" query={q} />
      <section className="table-card">
        <div className="table-tools"><span>{projects.length} visible projects</span><span>PostgreSQL-backed</span></div>
        {projects.length ? (
          <table aria-label="Projects"><thead><tr><th>ID</th><th>Name</th><th>Team</th><th>Visibility</th><th>Resources</th><th>Status</th></tr></thead><tbody>
            {projects.map((project) => <tr key={project.id}><td className="public-id"><Link href={`/projects/${project.public_id}`}>{project.public_id}</Link></td><td><Link className="row-link" href={`/projects/${project.public_id}`}>{project.name}</Link><small className="table-subline">Owner: {project.owner_name}</small></td><td>{project.team_name ?? "—"}</td><td><span className="badge">{project.visibility === "organization" ? "Institute" : project.visibility}</span></td><td>{project.oligo_count} oligos · {project.assay_count} assays</td><td><span className="badge">{project.status}</span></td></tr>)}
          </tbody></table>
        ) : <div className="empty"><strong>No visible projects</strong>Create a project or ask a project manager to add your membership.</div>}
      </section>
    </>
  );
}
