import Link from "next/link";
import { notFound } from "next/navigation";

import { removeTeamMember, setTeamMember, updateTeam } from "@/app/workspace/actions";
import { ConfirmRemoveButton } from "@/components/ConfirmRemoveButton";
import { PageHeader } from "@/components/PageHeader";
import { apiGetOptional, type TeamDetail, type UserSummary } from "@/lib/api";

const managerRoles = new Set(["admin", "team_manager"]);

export default async function TeamDetailPage({ params, searchParams }: { params: Promise<{ teamId: string }>; searchParams: Promise<{ updated?: string; membership?: string; error?: string }> }) {
  const { teamId } = await params;
  const state = await searchParams;
  const team = await apiGetOptional<TeamDetail>(`/workspace/teams/${encodeURIComponent(teamId)}`);
  if (!team) notFound();
  const canManage = Boolean(team.current_user_role && managerRoles.has(team.current_user_role));
  const candidates = canManage ? await apiGetOptional<UserSummary[]>("/workspace/users") : null;
  return (
    <>
      <PageHeader eyebrow="Workspace / team" title={team.name} description={team.description ?? "No team description yet."} />
      {state.updated ? <div className="success-notice" role="status">Team updated and audited.</div> : null}
      {state.membership ? <div className="success-notice" role="status">Team membership {state.membership} and audited.</div> : null}
      {state.error ? <div className="notice" role="alert">{state.error}</div> : null}
      <section className="stats" aria-label="Team summary">
        <div className="stat"><div className="stat-label">Members</div><div className="stat-value">{team.member_count}</div><div className="stat-detail">Explicit memberships</div></div>
        <div className="stat"><div className="stat-label">Projects</div><div className="stat-value">{team.projects.length}</div><div className="stat-detail">Visible team projects</div></div>
        <div className="stat"><div className="stat-label">Oligos</div><div className="stat-value">{team.oligo_count}</div><div className="stat-detail">Visible team-owned records</div></div>
        <div className="stat"><div className="stat-label">Assays</div><div className="stat-value">{team.assay_count}</div><div className="stat-detail">Visible team-owned designs</div></div>
      </section>
      <section className="workspace-grid">
        <div className="panel workspace-panel"><div className="panel-heading"><h2 className="panel-title">Members and roles</h2><p className="panel-copy">Permissions are enforced by FastAPI, not by this page.</p></div>
          <div className="member-list">{team.members.map((membership) => <div className="member-row" key={membership.user.id}><span className="member-avatar">{membership.user.initials}</span><span><strong>{membership.user.display_name}</strong><small>{membership.user.email}</small></span><span className="badge">{membership.role.replaceAll("_", " ")}</span>{canManage ? <form action={removeTeamMember.bind(null, team.id, membership.user.id)}><ConfirmRemoveButton /></form> : null}</div>)}</div>
          {canManage && candidates ? <form className="inline-admin-form" action={setTeamMember.bind(null, team.id)}><label><span>User</span><select name="user_id" required><option value="">Select user</option>{candidates.map((user) => <option value={user.id} key={user.id}>{user.display_name} · {user.email}</option>)}</select></label><label><span>Role</span><select name="role" defaultValue="member"><option value="admin">Admin</option><option value="team_manager">Team manager</option><option value="member">Member</option><option value="viewer">Viewer</option></select></label><button className="secondary-button" type="submit">Add or update</button></form> : null}
        </div>
        <div className="panel workspace-panel"><div className="panel-heading"><h2 className="panel-title">Team projects</h2><p className="panel-copy">Only projects visible to you are listed.</p></div><div className="linked-groups">{team.projects.length ? team.projects.map((project) => <Link href={`/projects/${project.public_id}`} key={project.public_id}>{project.public_id} · {project.name}</Link>) : <p>No team projects yet.</p>}</div><div className="truthful-gap"><strong>Later-domain attention</strong><span>Validation and stock alerts remain unavailable until their execution plans are implemented.</span></div></div>
      </section>
      {canManage ? <form className="record-form compact-form" action={updateTeam.bind(null, team.id)}><h2>Team settings</h2><div className="form-grid"><label className="field"><span>Name</span><input name="name" defaultValue={team.name} required /></label><label className="field checkbox-field"><input name="active" type="checkbox" defaultChecked={team.active} /><span>Active team</span></label><label className="field field-wide"><span>Description</span><textarea name="description" rows={3} defaultValue={team.description ?? ""} /></label></div><div className="form-actions"><button className="primary-button" type="submit">Save team</button></div></form> : null}
    </>
  );
}
