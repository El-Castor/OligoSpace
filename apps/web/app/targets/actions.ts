"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiWrite, type TargetSummary } from "@/lib/api";
import { actionError, optionalText, requiredText } from "@/lib/form-values";

function targetBody(formData: FormData) {
  return {
    name: requiredText(formData, "name"),
    target_type: requiredText(formData, "target_type"),
    organism_id: optionalText(formData, "organism_id"),
    gene_identifier: optionalText(formData, "gene_identifier"),
    transcript_identifier: optionalText(formData, "transcript_identifier"),
    description: optionalText(formData, "description"),
    reference_sequence: optionalText(formData, "reference_sequence"),
    visibility: requiredText(formData, "visibility"),
  };
}

export async function createTarget(formData: FormData) {
  let result: TargetSummary;
  try {
    result = await apiWrite<TargetSummary>("/registry/targets", "POST", targetBody(formData));
  } catch (error) {
    redirect(`/targets/new?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/");
  revalidatePath("/targets");
  redirect(`/targets/${result.public_id}`);
}

export async function updateTarget(publicId: string, formData: FormData) {
  let result: TargetSummary;
  try {
    result = await apiWrite<TargetSummary>(`/registry/targets/${publicId}`, "PATCH", {
      ...targetBody(formData),
      status: requiredText(formData, "status"),
    });
  } catch (error) {
    redirect(`/targets/${publicId}/edit?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/");
  revalidatePath("/targets");
  revalidatePath(`/targets/${publicId}`);
  redirect(`/targets/${result.public_id}?updated=1`);
}
