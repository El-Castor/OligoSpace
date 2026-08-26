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
  status: string;
}

export interface TargetSummary {
  id: string;
  public_id: string;
  name: string;
  target_type: string;
  gene_identifier: string | null;
  status: string;
}

export interface AssaySummary {
  id: string;
  public_id: string;
  name: string;
  expected_amplicon_length: number | null;
  status: string;
  version: number;
}

export interface DashboardSummary {
  oligos: number;
  assays: number;
  targets: number;
  projects: number;
  awaiting_validation: number | null;
  low_stock: number | null;
}

export async function apiGet<T>(path: string): Promise<T> {
  const session = developmentAuth ? null : await getServerSession(authOptions);
  const headers: HeadersInit = { Accept: "application/json" };
  if (session?.accessToken) headers.Authorization = `Bearer ${session.accessToken}`;
  const response = await fetch(`${apiBase}${path}`, { headers, cache: "no-store" });
  if (!response.ok) throw new Error(`API request failed with status ${response.status}`);
  return (await response.json()) as T;
}

export async function apiGetOptional<T>(path: string): Promise<T | null> {
  try {
    return await apiGet<T>(path);
  } catch {
    return null;
  }
}
