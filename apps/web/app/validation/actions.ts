"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiUpload, apiWrite, type AttachmentSummary, type ValidationSummary } from "@/lib/api";
import { actionError, optionalText, requiredText } from "@/lib/form-values";

function jsonObject(formData: FormData, name: string): Record<string, unknown> {
  const value = requiredText(formData, name) || "{}";
  const parsed: unknown = JSON.parse(value);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error(`${name} must be a JSON object`);
  }
  return parsed as Record<string, unknown>;
}

export async function createValidation(formData: FormData) {
  let result: ValidationSummary;
  try {
    const validatedAt = new Date(requiredText(formData, "validated_at"));
    if (Number.isNaN(validatedAt.valueOf())) throw new Error("Validation date is invalid.");
    result = await apiWrite<ValidationSummary>("/laboratory/validations", "POST", {
      assay_id: requiredText(formData, "assay_id"),
      experiment_run_id: optionalText(formData, "experiment_run_id"),
      status: requiredText(formData, "status"),
      conclusion: requiredText(formData, "conclusion"),
      measurements: jsonObject(formData, "measurements"),
      notes: optionalText(formData, "notes"),
      validated_at: validatedAt.toISOString(),
      supersedes_validation_public_id: optionalText(formData, "supersedes_validation_public_id"),
    });
  } catch (error) {
    redirect(`/validation/new?error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath("/");
  revalidatePath("/validation");
  revalidatePath("/experiments");
  redirect(`/validation/${result.public_id}`);
}

export async function uploadValidationAttachment(publicId: string, formData: FormData) {
  const file = formData.get("file");
  try {
    if (!(file instanceof File) || file.size === 0) throw new Error("Select an evidence file.");
    const upload = new FormData();
    upload.set("file", file);
    await apiUpload<AttachmentSummary>(`/laboratory/validation/${publicId}/attachments`, upload);
  } catch (error) {
    redirect(`/validation/${publicId}?attachmentError=${encodeURIComponent(actionError(error))}#evidence-files`);
  }
  revalidatePath(`/validation/${publicId}`);
  redirect(`/validation/${publicId}?attachment=uploaded#evidence-files`);
}
