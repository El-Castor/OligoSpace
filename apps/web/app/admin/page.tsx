import Link from "next/link";

import {
  createExperimentType,
  createOrganism,
  createTeam,
  createUser,
  updateExperimentType,
  updateUser,
} from "@/app/workspace/actions";
import { PageHeader } from "@/components/PageHeader";
import {
  apiGet,
  type CurrentUser,
  type ExperimentType,
  type Organism,
  type ProjectSummary,
  type TeamSummary,
  type UserSummary,
} from "@/lib/api";

export default async function AdminPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const state = await searchParams;
  const current = await apiGet<CurrentUser>("/me");
  if (current.role !== "admin") {
    return <><PageHeader eyebrow="System" title="Access denied" description="Administration requires the server-enforced administrator role." /><div className="notice" role="alert">Your current role is {current.role.replaceAll("_", " ")}. No administrative data was requested.</div></>;
  }
  const [users, teams, projects, experimentTypes, organisms] = await Promise.all([
    apiGet<UserSummary[]>("/workspace/admin/users"),
    apiGet<TeamSummary[]>("/workspace/teams"),
    apiGet<ProjectSummary[]>("/workspace/projects"),
    apiGet<ExperimentType[]>("/registry/experiment-types?active_only=false"),
    apiGet<Organism[]>("/registry/organisms"),
  ]);
  return (
    <>
      <PageHeader eyebrow="System" title="Administration" description="Manage projected identities, memberships, projects, configurable methods, and controlled vocabularies. Every mutation is authorized and audited by the API." />
      {state.error ? <div className="notice" role="alert">{state.error}</div> : null}
      {Object.keys(state).some((key) => key !== "error") ? <div className="success-notice" role="status">Administrative change persisted and audited.</div> : null}
      <nav className="admin-jump" aria-label="Administration sections"><a href="#users">Users</a><a href="#teams">Teams</a><a href="#projects">Projects</a><a href="#experiment-types">Experiment types</a><a href="#vocabularies">Controlled vocabularies</a></nav>

      <section className="admin-section" id="users"><div className="admin-heading"><div><p className="eyebrow">Identity</p><h2>Users</h2></div><span>{users.length} projections</span></div>
        <form className="inline-admin-form admin-create" action={createUser}><label><span>External identity ID</span><input name="external_identity_id" required /></label><label><span>Provider</span><input name="identity_provider" defaultValue="keycloak" required /></label><label><span>Email</span><input name="email" type="email" required /></label><label><span>Display name</span><input name="display_name" required /></label><label><span>First name</span><input name="first_name" /></label><label><span>Last name</span><input name="last_name" /></label><label><span>Global role</span><select name="global_role" defaultValue="member"><option value="admin">Admin</option><option value="team_manager">Team manager</option><option value="member">Member</option><option value="viewer">Viewer</option></select></label><button className="primary-button" type="submit">Create projection</button></form>
        <div className="admin-list">{users.map((user) => <form className="admin-row" action={updateUser.bind(null, user.id)} key={user.id}><span className="member-avatar">{user.initials}</span><span><strong>{user.display_name}</strong><small>{user.email}<br />{user.identity_provider} · {user.external_identity_id}</small></span><label><span>Role</span><select name="global_role" defaultValue={user.global_role}><option value="admin">Admin</option><option value="team_manager">Team manager</option><option value="member">Member</option><option value="viewer">Viewer</option></select></label><label className="checkbox-field"><input name="active" type="checkbox" defaultChecked={user.active} /><span>Active</span></label><button className="secondary-button" type="submit">Save</button></form>)}</div>
      </section>

      <section className="admin-section" id="teams"><div className="admin-heading"><div><p className="eyebrow">Collaboration</p><h2>Teams</h2></div><span>{teams.length} teams</span></div><form className="inline-admin-form" action={createTeam}><label><span>Name</span><input name="name" required /></label><label><span>Description</span><input name="description" /></label><button className="primary-button" type="submit">Create team</button></form><div className="admin-list">{teams.map((team) => <Link className="admin-link-row" href={`/team/${team.id}`} key={team.id}><span><strong>{team.name}</strong><small>{team.description ?? "No description"}</small></span><span>{team.member_count} members</span><span className="badge">{team.active ? "Active" : "Inactive"}</span></Link>)}</div></section>

      <section className="admin-section" id="projects"><div className="admin-heading"><div><p className="eyebrow">Workspaces</p><h2>Projects</h2></div><Link className="primary-button" href="/projects/new">Create project</Link></div><div className="admin-list">{projects.map((project) => <Link className="admin-link-row" href={`/projects/${project.public_id}`} key={project.id}><span><strong>{project.public_id} · {project.name}</strong><small>{project.owner_name} · {project.team_name ?? "No team"}</small></span><span>{project.member_count} members</span><span className="badge">{project.status}</span></Link>)}</div></section>

      <section className="admin-section" id="experiment-types"><div className="admin-heading"><div><p className="eyebrow">Configurable catalogue</p><h2>Experiment types</h2></div><span>{experimentTypes.length} methods</span></div><form className="inline-admin-form admin-create" action={createExperimentType}><label><span>Name</span><input name="name" required /></label><label><span>Slug</span><input name="slug" required pattern="[a-z0-9]+(?:-[a-z0-9]+)*" /></label><label><span>Description</span><input name="description" /></label><label><span>Allowed roles</span><input name="allowed_roles" required placeholder="forward_primer, reverse_primer" /></label><label><span>Required metadata JSON</span><textarea name="required_metadata" defaultValue="{}" /></label><label><span>Validation hints JSON</span><textarea name="recommended_validation_fields" defaultValue="{}" /></label><button className="primary-button" type="submit">Create method</button></form><div className="admin-list">{experimentTypes.map((type) => <form className="admin-row compact" action={updateExperimentType.bind(null, type.id)} key={type.id}><span><strong>{type.name}</strong><small>{type.slug} · {type.allowed_roles.join(", ") || "No roles configured"}</small></span><label className="checkbox-field"><input name="active" type="checkbox" defaultChecked={type.active} /><span>Active</span></label><button className="secondary-button" type="submit">Save state</button></form>)}</div></section>

      <section className="admin-section" id="vocabularies"><div className="admin-heading"><div><p className="eyebrow">Controlled vocabulary</p><h2>Organisms</h2></div><span>{organisms.length} entries</span></div><form className="inline-admin-form" action={createOrganism}><label><span>Scientific name</span><input name="scientific_name" required /></label><label><span>Common name</span><input name="common_name" /></label><label><span>Taxonomy ID</span><input name="taxonomy_id" /></label><button className="primary-button" type="submit">Add organism</button></form><div className="admin-list">{organisms.map((organism) => <div className="admin-link-row" key={organism.id}><span><strong><em>{organism.scientific_name}</em></strong><small>{organism.common_name ?? "No common name"}</small></span><span>{organism.taxonomy_id ? `Taxonomy ${organism.taxonomy_id}` : "No taxonomy ID"}</span></div>)}</div></section>
    </>
  );
}
