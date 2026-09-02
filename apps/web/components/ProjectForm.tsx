import Link from "next/link";

import type { ProjectSummary, TeamSummary } from "@/lib/api";

type FormAction = (formData: FormData) => void | Promise<void>;

export function ProjectForm({
  action,
  teams,
  project,
  error,
}: {
  action: FormAction;
  teams: TeamSummary[];
  project?: ProjectSummary;
  error?: string;
}) {
  return (
    <form className="record-form" action={action}>
      {error ? <div className="notice" role="alert">{error}</div> : null}
      <div className="form-grid">
        <label className="field">
          <span>Name <strong aria-hidden="true">*</strong></span>
          <input name="name" required maxLength={200} defaultValue={project?.name} />
        </label>
        <label className="field">
          <span>Owning team</span>
          <select name="team_id" defaultValue={project?.team_id ?? ""}>
            <option value="">No team</option>
            {teams.map((team) => <option value={team.id} key={team.id}>{team.name}</option>)}
          </select>
        </label>
        <label className="field">
          <span>Visibility</span>
          <select name="visibility" defaultValue={project?.visibility ?? "private"}>
            <option value="private">Private</option>
            <option value="project">Project members</option>
            <option value="team">Team</option>
            <option value="organization">Institute</option>
          </select>
          <small>Team visibility requires an owning team. Membership and access are enforced by the API.</small>
        </label>
        {project ? (
          <label className="field">
            <span>Status</span>
            <select name="status" defaultValue={project.status}>
              <option value="active">Active</option>
              <option value="deprecated">Deprecated</option>
              <option value="archived">Archived</option>
            </select>
          </label>
        ) : null}
        <label className="field field-wide">
          <span>Description</span>
          <textarea name="description" rows={5} defaultValue={project?.description ?? ""} />
        </label>
      </div>
      <div className="form-actions">
        <button className="primary-button" type="submit">{project ? "Save project" : "Create project"}</button>
        <Link className="secondary-button" href={project ? `/projects/${project.public_id}` : "/projects"}>Cancel</Link>
      </div>
    </form>
  );
}
