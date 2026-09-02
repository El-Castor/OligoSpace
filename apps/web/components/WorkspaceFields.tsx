import type { WorkspaceChoices } from "@/lib/api";

export function WorkspaceFields({
  choices,
  visibility = "private",
  teamId,
  projectId,
}: {
  choices: WorkspaceChoices;
  visibility?: string;
  teamId?: string | null;
  projectId?: string | null;
}) {
  return (
    <>
      <label className="field"><span>Visibility</span><select name="visibility" defaultValue={visibility}><option value="private">Private</option><option value="project">Project</option><option value="team">Team</option><option value="organization">Institute</option></select><small>Project and Team visibility require the corresponding workspace below.</small></label>
      <label className="field"><span>Owning team</span><select name="owner_team_id" defaultValue={teamId ?? ""}><option value="">No team</option>{choices.teams.map((team) => <option value={team.id} key={team.id}>{team.name}</option>)}</select></label>
      <label className="field"><span>Project</span><select name="owner_project_id" defaultValue={projectId ?? ""}><option value="">No project</option>{choices.projects.map((project) => <option value={project.id} key={project.id}>{project.public_id} · {project.name}</option>)}</select></label>
    </>
  );
}
