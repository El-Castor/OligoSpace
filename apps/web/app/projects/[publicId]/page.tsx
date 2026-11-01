import { SubmitButton } from "@/components/SubmitButton";
import Link from "next/link";
import { notFound } from "next/navigation";

import { removeProjectMember, setProjectMember } from "@/app/workspace/actions";
import { ConfirmRemoveButton } from "@/components/ConfirmRemoveButton";
import { PageHeader } from "@/components/PageHeader";
import { apiGetOptional, type ProjectDetail, type UserSummary } from "@/lib/api";

const managerRoles = new Set(["admin", "team_manager"]);

export default async function ProjectDetailPage({ params, searchParams }: { params: Promise<{ publicId: string }>; searchParams: Promise<{ created?: string; updated?: string; membership?: string; error?: string }> }) {
  const { publicId } = await params;
  const state = await searchParams;
  const project = await apiGetOptional<ProjectDetail>(`/workspace/projects/${encodeURIComponent(publicId)}`);
  if (!project) notFound();
  const canManage = Boolean(project.current_user_role && managerRoles.has(project.current_user_role));
  const candidates = canManage ? await apiGetOptional<UserSummary[]>("/workspace/users") : null;
  return (
    <>
      <PageHeader eyebrow={`Workspace / ${project.public_id}`} title={project.name} description={project.description ?? "No project description yet."} action={canManage ? <Link className="primary-button" href={`/projects/${project.public_id}/edit`}>Edit project</Link> : undefined} />
      {state.created ? <div className="success-notice" role="status">Project created in PostgreSQL.</div> : null}
      {state.updated ? <div className="success-notice" role="status">Project updated and audited.</div> : null}
      {state.membership ? <div className="success-notice" role="status">Project membership {state.membership} and audited.</div> : null}
      {state.error ? <div className="notice" role="alert">{state.error}</div> : null}
      <dl className="record-details">
        <div className="record-field"><dt>Public ID</dt><dd>{project.public_id}</dd></div>
        <div className="record-field"><dt>Owner</dt><dd>{project.owner_name}</dd></div>
        <div className="record-field"><dt>Team</dt><dd>{project.team_name ?? "No team"}</dd></div>
        <div className="record-field"><dt>Visibility</dt><dd><span className="badge">{project.visibility === "organization" ? "Institute" : project.visibility}</span></dd></div>
        <div className="record-field"><dt>Status</dt><dd><span className="badge">{project.status}</span></dd></div>
        <div className="record-field"><dt>Members</dt><dd>{project.member_count}</dd></div>
        <div className="record-field"><dt>Oligos</dt><dd>{project.oligo_count}</dd></div>
        <div className="record-field"><dt>Assays</dt><dd>{project.assay_count}</dd></div>
      </dl>
      <section className="workspace-grid">
        <div className="panel workspace-panel"><div className="panel-heading"><h2 className="panel-title">Members</h2><p className="panel-copy">Explicit project roles control project-visible records.</p></div>
          <div className="member-list">{project.members.map((membership) => <div className="member-row" key={membership.user.id}><span className="member-avatar">{membership.user.initials}</span><span><strong>{membership.user.display_name}</strong><small>{membership.user.email}</small></span><span className="badge">{membership.role.replaceAll("_", " ")}</span>{canManage && membership.user.id !== project.created_by_id ? <form action={removeProjectMember.bind(null, project.public_id, membership.user.id)}><ConfirmRemoveButton /></form> : null}</div>)}</div>
          {canManage && candidates ? <form className="inline-admin-form" action={setProjectMember.bind(null, project.public_id)}><label><span>User</span><select name="user_id" required><option value="">Select user</option>{candidates.map((user) => <option value={user.id} key={user.id}>{user.display_name} · {user.email}</option>)}</select></label><label><span>Role</span><select name="role" defaultValue="member"><option value="admin">Admin</option><option value="team_manager">Team manager</option><option value="member">Member</option><option value="viewer">Viewer</option></select></label><SubmitButton className="secondary-button">Add or update</SubmitButton></form> : null}
        </div>
        <div className="panel workspace-panel"><div className="panel-heading"><h2 className="panel-title">Linked resources</h2><p className="panel-copy">Persisted project relationships only.</p></div><div className="linked-groups"><h3>Oligos</h3>{project.oligos.length ? project.oligos.map((item) => <Link href={`/oligos/${item.public_id}`} key={item.public_id}>{item.public_id} · {item.name}</Link>) : <p>No linked oligos.</p>}<h3>Assays</h3>{project.assays.length ? project.assays.map((item) => <Link href={`/assays/${item.public_id}`} key={item.public_id}>{item.public_id} · {item.name}</Link>) : <p>No linked assays.</p>}</div></div>
      </section>
    </>
  );
}
