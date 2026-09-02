"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiWrite, type OligoCreateResult, type OligoSummary } from "@/lib/api";
import { actionError, optionalText, requiredText } from "@/lib/form-values";

export async function createOligo(formData: FormData) {
  let result: OligoCreateResult;
  try {
    result = await apiWrite<OligoCreateResult>("/registry/oligos", "POST", {
      name: requiredText(formData, "name"),
      sequence: requiredText(formData, "sequence"),
      oligo_type: requiredText(formData, "oligo_type"),
      description: optionalText(formData, "description"),
      notes: optionalText(formData, "notes"),
      owner_team_id: optionalText(formData, "owner_team_id"),
      owner_project_id: optionalText(formData, "owner_project_id"),
      visibility: requiredText(formData, "visibility"),
    });
  } catch (error) {
    redirect(`/oligos/new?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/");
  revalidatePath("/oligos");
  redirect(`/oligos/${result.oligo.public_id}${result.warnings.length ? "?warning=reverse-complement" : ""}`);
}

export async function updateOligo(publicId: string, formData: FormData) {
  let result: OligoSummary;
  try {
    result = await apiWrite<OligoSummary>(`/registry/oligos/${publicId}`, "PATCH", {
      name: requiredText(formData, "name"),
      oligo_type: requiredText(formData, "oligo_type"),
      description: optionalText(formData, "description"),
      notes: optionalText(formData, "notes"),
      owner_team_id: optionalText(formData, "owner_team_id"),
      owner_project_id: optionalText(formData, "owner_project_id"),
      visibility: requiredText(formData, "visibility"),
      status: requiredText(formData, "status"),
    });
  } catch (error) {
    redirect(`/oligos/${publicId}/edit?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/");
  revalidatePath("/oligos");
  revalidatePath(`/oligos/${publicId}`);
  redirect(`/oligos/${result.public_id}?updated=1`);
}
