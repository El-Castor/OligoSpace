import { createHmac } from "node:crypto";
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
  owner_team_id: string | null;
  owner_project_id: string | null;
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
  owner_team_id: string | null;
  owner_project_id: string | null;
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

export interface AttachmentSummary {
  id: string;
  public_id: string;
  experiment_run_id: string | null;
  validation_id: string | null;
  object_key: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  uploaded_by_id: string;
  scan_status: string;
  publication_status: string;
  replaces_attachment_id: string | null;
  removed_at: string | null;
  removed_by_id: string | null;
  created_at: string;
}

export interface ValidationSummary {
  id: string;
  public_id: string;
  assay_id: string;
  experiment_run_id: string | null;
  status: string;
  conclusion: string;
  measurements: Record<string, unknown>;
  notes: string | null;
  validated_by_id: string;
  validated_at: string;
  supersedes_validation_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ValidationDetail extends ValidationSummary {
  attachments: AttachmentSummary[];
}

export interface ExperimentRunSummary {
  id: string;
  public_id: string;
  assay_id: string;
  assay_version: number;
  project_id: string | null;
  owner_team_id: string | null;
  operator_id: string;
  performed_at: string;
  protocol_name: string | null;
  protocol_version: string | null;
  conditions: Record<string, unknown>;
  input_metadata: Record<string, unknown>;
  notes: string | null;
  visibility: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ExperimentRunDetail extends ExperimentRunSummary {
  validations: ValidationSummary[];
  attachments: AttachmentSummary[];
}

export interface ExperimentType {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  allowed_roles: string[];
  required_metadata: Record<string, unknown>;
  recommended_validation_fields: Record<string, unknown>;
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

export interface CurrentTeam {
  id: string;
  name: string;
  role: string;
}

export interface CurrentUser {
  id: string;
  organization_id: string;
  organization_name: string;
  email: string;
  display_name: string;
  first_name: string | null;
  last_name: string | null;
  avatar_url: string | null;
  initials: string;
  identity_provider: string;
  external_identity_id: string;
  active: boolean;
  role: string;
  development_identity: boolean;
  teams: CurrentTeam[];
  created_at: string;
  last_login_at: string | null;
}

export interface UserSummary {
  id: string;
  external_identity_id: string;
  identity_provider: string;
  email: string;
  display_name: string;
  first_name: string | null;
  last_name: string | null;
  avatar_url: string | null;
  initials: string;
  active: boolean;
  global_role: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export interface MembershipSummary {
  user: UserSummary;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface TeamSummary {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  active: boolean;
  member_count: number;
  current_user_role: string | null;
  created_at: string;
  updated_at: string;
}

export interface TeamDetail extends TeamSummary {
  members: MembershipSummary[];
  projects: Array<{ public_id: string; name: string; status: string }>;
  assay_count: number;
  oligo_count: number;
}

export interface ProjectSummary {
  id: string;
  public_id: string;
  organization_id: string;
  team_id: string | null;
  team_name: string | null;
  name: string;
  description: string | null;
  visibility: string;
  status: string;
  created_by_id: string;
  owner_name: string;
  current_user_role: string | null;
  member_count: number;
  oligo_count: number;
  assay_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends ProjectSummary {
  members: MembershipSummary[];
  oligos: Array<{ public_id: string; name: string; status: string }>;
  assays: Array<{ public_id: string; name: string; status: string }>;
}

export interface WorkspaceChoices {
  teams: TeamSummary[];
  projects: ProjectSummary[];
}

export interface PersonalizedDashboard {
  my_oligos: number;
  my_assays: number;
  my_projects: number;
  team_shared_oligos: number;
  visible_targets: number;
  visible_projects: number;
  recent_items: Array<{ entity_type: string; public_id: string; name: string; created_at: string }>;
  recent_activity: Array<{ action: string; entity_type: string; entity_id: string; occurred_at: string }>;
  awaiting_validation: number | null;
  low_stock: number | null;
}

export interface ScientificAttemptSummary {
  id: string;
  attempt_number: number;
  state: string;
  started_at: string;
  completed_at: string | null;
  retryable: boolean;
  tool_version: string | null;
  worker_version: string | null;
  wrapper_contract_version: string | null;
  build_identity: string | null;
  error_code: string | null;
  error_summary: string | null;
}

export interface ScientificResultSummary {
  result_schema_version: string;
  payload: Record<string, unknown>;
  warnings: Array<Record<string, unknown>>;
  algorithm: string;
  tool_version: string;
  tool_source_sha256: string;
  worker_version: string;
  wrapper_contract_version: string;
  build_identity: string;
  started_at: string;
  completed_at: string;
  executed_at: string;
}

export interface ScientificJobSummary {
  id: string;
  public_id: string;
  requester_id: string;
  kind: string;
  state: string;
  oligo_id: string | null;
  assay_id: string | null;
  forward_oligo_id: string | null;
  reverse_oligo_id: string | null;
  assay_version: number | null;
  input_snapshot: Record<string, unknown>;
  input_sha256: string;
  requested_parameters: Record<string, unknown>;
  effective_parameters: Record<string, unknown>;
  parameter_schema_version: string;
  execution_fingerprint: string;
  celery_task_id: string | null;
  attempt_count: number;
  max_attempts: number;
  queued_at: string;
  started_at: string | null;
  completed_at: string | null;
  last_error_code: string | null;
  last_error_summary: string | null;
  created_at: string;
  updated_at: string;
  attempts: ScientificAttemptSummary[];
  result: ScientificResultSummary | null;
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
  const session = await getServerSession(authOptions);
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (developmentAuth) {
    const userId = session?.user?.id;
    const secret = process.env.DEVELOPMENT_AUTH_SECRET;
    if (!userId || !secret) {
      throw new ApiError("An explicit development session is required.", 401, "development_session_required");
    }
    headers.set("X-OligoSpace-Development-User", userId);
    headers.set("X-OligoSpace-Development-Auth", createHmac("sha256", secret).update(userId).digest("hex"));
  } else if (session?.accessToken) {
    headers.set("Authorization", `Bearer ${session.accessToken}`);
  } else {
    throw new ApiError("Authentication is required.", 401, "authentication_required");
  }
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = errorDetail(await response.json().catch(() => null));
    throw new ApiError(detail.message, response.status, detail.code);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

export async function apiWrite<T>(
  path: string,
  method: "POST" | "PATCH" | "PUT",
  body: Record<string, unknown>,
  headers?: HeadersInit,
): Promise<T> {
  return apiRequest<T>(path, {
    method,
    headers: { "Content-Type": "application/json", ...Object.fromEntries(new Headers(headers)) },
    body: JSON.stringify(body),
  });
}

export async function apiUpload<T>(path: string, body: FormData): Promise<T> {
  return apiRequest<T>(path, { method: "POST", body });
}

export async function apiDelete(path: string): Promise<void> {
  await apiRequest<unknown>(path, { method: "DELETE" });
}

export async function apiGetOptional<T>(path: string): Promise<T | null> {
  try {
    return await apiGet<T>(path);
  } catch {
    return null;
  }
}
