import { ApiError } from "@/lib/api";

export function requiredText(formData: FormData, name: string): string {
  return String(formData.get(name) ?? "").trim();
}

export function optionalText(formData: FormData, name: string): string | null {
  const value = requiredText(formData, name);
  return value || null;
}

export function optionalNumber(formData: FormData, name: string): number | null {
  const value = optionalText(formData, name);
  if (value === null) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function actionError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "The registry could not save this record. Check the API and try again.";
}
