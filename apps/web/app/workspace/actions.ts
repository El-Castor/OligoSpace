"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  apiDelete,
  apiWrite,
  type ExperimentType,
  type Organism,
  type ProjectSummary,
  type TeamSummary,
  type UserSummary,
} from "@/lib/api";
import { actionError, optionalText, requiredText } from "@/lib/form-values";

function checked(formData: FormData, name: string): boolean {
  return formData.get(name) === "on" || formData.get(name) === "true";
}

function jsonObject(formData: FormData, name: string): Record<string, unknown> {
  const value = optionalText(formData, name);
  if (!value) return {};
  const parsed = JSON.parse(value) as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error(`${name.replaceAll("_", " ")} must be a JSON object.`);
  }
  return parsed as Record<string, unknown>;
}

export async function updateProfile(formData: FormData) {
  try {
    await apiWrite<UserSummary>("/workspace/profile", "PATCH", {
      display_name: requiredText(formData, "display_name"),
      first_name: optionalText(formData, "first_name"),
      last_name: optionalText(formData, "last_name"),
      avatar_url: optionalText(formData, "avatar_url"),
    });
  } catch (error) {
    redirect(`/profile?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/profile");
  revalidatePath("/", "layout");
  redirect("/profile?updated=1");
}

export async function createTeam(formData: FormData) {
  let team: TeamSummary;
  try {
    team = await apiWrite<TeamSummary>("/workspace/teams", "POST", {
      name: requiredText(formData, "name"),
      description: optionalText(formData, "description"),
    });
  } catch (error) {
    redirect(`/admin?error=${encodeURIComponent(actionError(error))}#teams`);
  }
  revalidatePath("/team");
  revalidatePath("/admin");
  redirect(`/team/${team.id}?created=1`);
}

export async function updateTeam(teamId: string, formData: FormData) {
  try {
    await apiWrite<TeamSummary>(`/workspace/teams/${teamId}`, "PATCH", {
      name: requiredText(formData, "name"),
      description: optionalText(formData, "description"),
      active: checked(formData, "active"),
    });
  } catch (error) {
    redirect(`/team/${teamId}?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/team");
  revalidatePath(`/team/${teamId}`);
  redirect(`/team/${teamId}?updated=1`);
}

export async function setTeamMember(teamId: string, formData: FormData) {
  try {
    const userId = requiredText(formData, "user_id");
    await apiWrite(`/workspace/teams/${teamId}/members/${userId}`, "PUT", {
      role: requiredText(formData, "role"),
    });
  } catch (error) {
    redirect(`/team/${teamId}?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath(`/team/${teamId}`);
  redirect(`/team/${teamId}?membership=updated`);
}

export async function removeTeamMember(teamId: string, userId: string) {
  try {
    await apiDelete(`/workspace/teams/${teamId}/members/${userId}`);
  } catch (error) {
    redirect(`/team/${teamId}?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath(`/team/${teamId}`);
  redirect(`/team/${teamId}?membership=removed`);
}

export async function createProject(formData: FormData) {
  let project: ProjectSummary;
  try {
    project = await apiWrite<ProjectSummary>("/workspace/projects", "POST", {
      name: requiredText(formData, "name"),
      description: optionalText(formData, "description"),
      team_id: optionalText(formData, "team_id"),
      visibility: requiredText(formData, "visibility"),
    });
  } catch (error) {
    redirect(`/projects/new?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/");
  revalidatePath("/projects");
  redirect(`/projects/${project.public_id}?created=1`);
}

export async function updateProject(publicId: string, formData: FormData) {
  try {
    await apiWrite<ProjectSummary>(`/workspace/projects/${publicId}`, "PATCH", {
      name: requiredText(formData, "name"),
      description: optionalText(formData, "description"),
      team_id: optionalText(formData, "team_id"),
      visibility: requiredText(formData, "visibility"),
      status: requiredText(formData, "status"),
    });
  } catch (error) {
    redirect(`/projects/${publicId}/edit?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/");
  revalidatePath("/projects");
  revalidatePath(`/projects/${publicId}`);
  redirect(`/projects/${publicId}?updated=1`);
}

export async function setProjectMember(publicId: string, formData: FormData) {
  try {
    const userId = requiredText(formData, "user_id");
    await apiWrite(`/workspace/projects/${publicId}/members/${userId}`, "PUT", {
      role: requiredText(formData, "role"),
    });
  } catch (error) {
    redirect(`/projects/${publicId}?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath(`/projects/${publicId}`);
  redirect(`/projects/${publicId}?membership=updated`);
}

export async function removeProjectMember(publicId: string, userId: string) {
  try {
    await apiDelete(`/workspace/projects/${publicId}/members/${userId}`);
  } catch (error) {
    redirect(`/projects/${publicId}?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath(`/projects/${publicId}`);
  redirect(`/projects/${publicId}?membership=removed`);
}

export async function createUser(formData: FormData) {
  try {
    await apiWrite<UserSummary>("/workspace/admin/users", "POST", {
      external_identity_id: requiredText(formData, "external_identity_id"),
      identity_provider: requiredText(formData, "identity_provider"),
      email: requiredText(formData, "email"),
      display_name: requiredText(formData, "display_name"),
      first_name: optionalText(formData, "first_name"),
      last_name: optionalText(formData, "last_name"),
      global_role: requiredText(formData, "global_role"),
      active: true,
    });
  } catch (error) {
    redirect(`/admin?error=${encodeURIComponent(actionError(error))}#users`);
  }
  revalidatePath("/admin");
  redirect("/admin?user=created#users");
}

export async function updateUser(userId: string, formData: FormData) {
  try {
    await apiWrite<UserSummary>(`/workspace/admin/users/${userId}`, "PATCH", {
      global_role: requiredText(formData, "global_role"),
      active: checked(formData, "active"),
    });
  } catch (error) {
    redirect(`/admin?error=${encodeURIComponent(actionError(error))}#users`);
  }
  revalidatePath("/admin");
  redirect("/admin?user=updated#users");
}

export async function createExperimentType(formData: FormData) {
  try {
    await apiWrite<ExperimentType>("/registry/experiment-types", "POST", {
      name: requiredText(formData, "name"),
      slug: requiredText(formData, "slug"),
      description: optionalText(formData, "description"),
      allowed_roles: requiredText(formData, "allowed_roles").split(",").map((item) => item.trim()).filter(Boolean),
      required_metadata: jsonObject(formData, "required_metadata"),
      recommended_validation_fields: jsonObject(formData, "recommended_validation_fields"),
      active: true,
    });
  } catch (error) {
    redirect(`/admin?error=${encodeURIComponent(actionError(error))}#experiment-types`);
  }
  revalidatePath("/admin");
  redirect("/admin?experimentType=created#experiment-types");
}

export async function updateExperimentType(experimentTypeId: string, formData: FormData) {
  try {
    await apiWrite<ExperimentType>(`/registry/experiment-types/${experimentTypeId}`, "PATCH", {
      active: checked(formData, "active"),
    });
  } catch (error) {
    redirect(`/admin?error=${encodeURIComponent(actionError(error))}#experiment-types`);
  }
  revalidatePath("/admin");
  redirect("/admin?experimentType=updated#experiment-types");
}

export async function createOrganism(formData: FormData) {
  try {
    await apiWrite<Organism>("/registry/organisms", "POST", {
      scientific_name: requiredText(formData, "scientific_name"),
      common_name: optionalText(formData, "common_name"),
      taxonomy_id: optionalText(formData, "taxonomy_id"),
    });
  } catch (error) {
    redirect(`/admin?error=${encodeURIComponent(actionError(error))}#vocabularies`);
  }
  revalidatePath("/admin");
  redirect("/admin?organism=created#vocabularies");
}
