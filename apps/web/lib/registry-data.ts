import { apiGet, ApiError } from "@/lib/api";
import { registryFailure } from "@/lib/registry-page";

export async function registryData<T>(path: string): Promise<{ result: T | null; error?: string }> {
  try { return { result: await apiGet<T>(path) }; }
  catch (error) { return { result: null, error: registryFailure(error instanceof ApiError ? error.status : undefined) }; }
}
