import { getServerSession } from "next-auth";

import { authOptions, developmentAuth } from "@/lib/auth";

const apiBase = process.env.API_INTERNAL_URL ?? "http://api:8000/api/v1";

export interface PageResult<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface OligoSummary {
  id: string;
  public_id: string;
  name: string;
  normalized_sequence: string;
  sequence_length: number;
  gc_percent: number | null;
  melting_temperature_c: number | null;
  description: string | null;
  notes: string | null;
  oligo_type: string;
  reverse_complement: string;
  molecular_weight_g_mol: number | null;
  calculation_provenance: Record<string, unknown>;
  visibility: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TargetSummary {
  id: string;
  public_id: string;
  name: string;
  target_type: string;
  organism_id: string | null;
  reference_genome_id: string | null;
  gene_identifier: string | null;
  transcript_identifier: string | null;
  description: string | null;
  reference_sequence: string | null;
  visibility: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AssaySummary {
  id: string;
  public_id: string;
  name: string;
  experiment_type_id: string;
  target_id: string | null;
  organism_id: string | null;
  project_id: string | null;
  owner_team_id: string | null;
  expected_product: string | null;
  expected_amplicon_length: number | null;
  recommended_annealing_temperature_c: number | null;
  protocol_notes: string | null;
  method_metadata: Record<string, unknown>;
  visibility: string;
  status: string;
  version: number;
  oligos: Array<{ oligo_id: string; role: string; label: string | null }>;
  created_at: string;
  updated_at: string;
}

export interface ExperimentType {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  allowed_roles: string[];
  active: boolean;
}

export interface Organism {
  id: string;
  scientific_name: string;
  common_name: string | null;
  taxonomy_id: string | null;
}

export interface OligoCreateResult {
  oligo: OligoSummary;
  warnings: string[];
}

export interface DashboardSummary {
  oligos: number;
  assays: number;
  targets: number;
  projects: number;
  awaiting_validation: number | null;
  low_stock: number | null;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function errorDetail(payload: unknown): { code: string; message: string } {
  if (typeof payload !== "object" || payload === null || !("detail" in payload)) {
    return { code: "api_error", message: "The registry request failed." };
  }
  const detail = payload.detail;
  if (typeof detail === "string") return { code: "api_error", message: detail };
  if (typeof detail === "object" && detail !== null) {
    const code = "code" in detail && typeof detail.code === "string" ? detail.code : "api_error";
    const message = "message" in detail && typeof detail.message === "string" ? detail.message : code.replaceAll("_", " ");
    return { code, message };
  }
  return { code: "api_error", message: "The registry request failed." };
}

async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const session = developmentAuth ? null : await getServerSession(authOptions);
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (session?.accessToken) headers.set("Authorization", `Bearer ${session.accessToken}`);
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = errorDetail(await response.json().catch(() => null));
    throw new ApiError(detail.message, response.status, detail.code);
  }
  return (await response.json()) as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

export async function apiWrite<T>(
  path: string,
  method: "POST" | "PATCH",
  body: Record<string, unknown>,
): Promise<T> {
  return apiRequest<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function apiGetOptional<T>(path: string): Promise<T | null> {
  try {
    return await apiGet<T>(path);
  } catch {
    return null;
  }
}
