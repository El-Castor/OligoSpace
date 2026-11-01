import { ScientificForm } from "@/components/ScientificForm";
import { FormSection } from "@/components/FormSection";
import { SubmitButton } from "@/components/SubmitButton";
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
    <ScientificForm action={action} error={error}>
      <FormSection title="Project identity" description="Visibility and membership remain enforced by the server.">
        <label className="field">
          <span>Name <strong aria-hidden="true">*</strong></span>
          <input name="name" required maxLength={200} defaultValue={project?.name} />
        </label>
      </FormSection>
      <FormSection title="Access and lifecycle" description="Membership and visibility remain server-enforced.">
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
      </FormSection>
      <div className="form-actions">
        <SubmitButton>{project ? "Save project" : "Create project"}</SubmitButton>
        <Link className="secondary-button" href={project ? `/projects/${project.public_id}` : "/projects"}>Cancel</Link>
      </div>
    </ScientificForm>
  );
}
