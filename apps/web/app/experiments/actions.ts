"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiUpload, apiWrite, type AttachmentSummary, type ExperimentRunSummary } from "@/lib/api";
import { actionError, optionalText, requiredText } from "@/lib/form-values";

function jsonObject(formData: FormData, name: string): Record<string, unknown> {
  const value = requiredText(formData, name) || "{}";
  const parsed: unknown = JSON.parse(value);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error(`${name} must be a JSON object`);
  }
  return parsed as Record<string, unknown>;
}

function isoDate(formData: FormData, name: string): string {
  const date = new Date(requiredText(formData, name));
  if (Number.isNaN(date.valueOf())) throw new Error(`${name} is invalid`);
  return date.toISOString();
}

export async function createExperimentRun(formData: FormData) {
  let result: ExperimentRunSummary;
  try {
    result = await apiWrite<ExperimentRunSummary>("/laboratory/runs", "POST", {
      assay_id: requiredText(formData, "assay_id"),
      performed_at: isoDate(formData, "performed_at"),
      project_id: optionalText(formData, "owner_project_id"),
      owner_team_id: optionalText(formData, "owner_team_id"),
      protocol_name: optionalText(formData, "protocol_name"),
      protocol_version: optionalText(formData, "protocol_version"),
      conditions: jsonObject(formData, "conditions"),
      input_metadata: jsonObject(formData, "input_metadata"),
      notes: optionalText(formData, "notes"),
      visibility: requiredText(formData, "visibility"),
    });
  } catch (error) {
    redirect(`/experiments/new?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/");
  revalidatePath("/experiments");
  redirect(`/experiments/${result.public_id}`);
}

export async function updateExperimentRun(publicId: string, formData: FormData) {
  try {
    await apiWrite<ExperimentRunSummary>(`/laboratory/runs/${publicId}`, "PATCH", {
      notes: optionalText(formData, "notes"),
      status: requiredText(formData, "status"),
    });
  } catch (error) {
    redirect(`/experiments/${publicId}?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath(`/experiments/${publicId}`);
  redirect(`/experiments/${publicId}?updated=1`);
}

export async function uploadRunAttachment(publicId: string, formData: FormData) {
  const file = formData.get("file");
  try {
    if (!(file instanceof File) || file.size === 0) throw new Error("Select an evidence file.");
    const upload = new FormData();
    upload.set("file", file);
    await apiUpload<AttachmentSummary>(`/laboratory/run/${publicId}/attachments`, upload);
  } catch (error) {
    redirect(`/experiments/${publicId}?attachmentError=${encodeURIComponent(actionError(error))}#evidence-files`);
  }
  revalidatePath(`/experiments/${publicId}`);
  redirect(`/experiments/${publicId}?attachment=uploaded#evidence-files`);
}
