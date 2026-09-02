"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiWrite, type AssaySummary } from "@/lib/api";
import { actionError, optionalNumber, optionalText, requiredText } from "@/lib/form-values";

function assayBody(formData: FormData) {
  const oligoIds = formData.getAll("oligo_id").map(String);
  const roles = formData.getAll("role").map(String);
  const labels = formData.getAll("label").map(String);
  const oligos = oligoIds.flatMap((oligoId, index) =>
    oligoId && roles[index]
      ? [{ oligo_id: oligoId, role: roles[index], label: labels[index]?.trim() || null }]
      : [],
  );
  return {
    name: requiredText(formData, "name"),
    experiment_type_id: requiredText(formData, "experiment_type_id"),
    target_id: optionalText(formData, "target_id"),
    owner_team_id: optionalText(formData, "owner_team_id"),
    project_id: optionalText(formData, "owner_project_id"),
    expected_product: optionalText(formData, "expected_product"),
    expected_amplicon_length: optionalNumber(formData, "expected_amplicon_length"),
    recommended_annealing_temperature_c: optionalNumber(formData, "recommended_annealing_temperature_c"),
    protocol_notes: optionalText(formData, "protocol_notes"),
    visibility: requiredText(formData, "visibility"),
    oligos,
  };
}

export async function createAssay(formData: FormData) {
  let result: AssaySummary;
  try {
    result = await apiWrite<AssaySummary>("/registry/assays", "POST", assayBody(formData));
  } catch (error) {
    redirect(`/assays/new?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/");
  revalidatePath("/assays");
  redirect(`/assays/${result.public_id}`);
}

export async function updateAssay(publicId: string, formData: FormData) {
  let result: AssaySummary;
  try {
    result = await apiWrite<AssaySummary>(`/registry/assays/${publicId}`, "PATCH", {
      ...assayBody(formData),
      status: requiredText(formData, "status"),
    });
  } catch (error) {
    redirect(`/assays/${publicId}/edit?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/");
  revalidatePath("/assays");
  revalidatePath(`/assays/${publicId}`);
  redirect(`/assays/${result.public_id}?updated=1`);
}
