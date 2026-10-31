import Link from "next/link";

import { registryData } from "@/lib/registry-data";
import { registryOffset } from "@/lib/registry-page";
import { ScientificValue } from "@/components/ScientificValue";
import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { RegistryTable } from "@/components/RegistryTable";
import { apiGetOptional, type AssaySummary, type ExperimentRunSummary, type PageResult } from "@/lib/api";

export default async function ExperimentsPage({ searchParams }: { searchParams: Promise<{ q?: string; offset?: string }> }) {
  const params = await searchParams;
  const query = params.q?.trim() ?? "";
  const offset = registryOffset(params.offset);
  const [loaded, assayPage] = await Promise.all([
    registryData<PageResult<ExperimentRunSummary>>(`/laboratory/runs?q=${encodeURIComponent(query)}&offset=${offset}`),
    apiGetOptional<PageResult<AssaySummary>>("/registry/assays?limit=200"),
  ]);
  const { result, error } = loaded;
  const assays = new Map(assayPage?.items.map((assay) => [assay.id, assay]));
  const items = result?.items ?? [];
  return <><PageHeader eyebrow="Research / evidence" title="Experiment runs" description="Repeatable executions of versioned assays. Conditions and observations are user-provided evidence, never changes to the assay definition." action={<Link className="primary-button" href="/experiments/new">New experiment run</Link>} /><RegistrySearch action="/experiments" query={query} /><RegistryTable shown={items.length} label="Experiments" query={query} path="/experiments" offset={result?.offset ?? offset} limit={result?.limit ?? 50} error={error} count={result?.total ?? 0} columns={["ID", "Assay version", "Performed", "Protocol", "Status"]}>{items.map((run) => { const assay = assays.get(run.assay_id); return <tr key={run.id}><td className="public-id"><ScientificValue value={run.public_id} href={`/experiments/${run.public_id}`} copy /></td><td>{assay?.name ?? "Accessible assay"} · v{run.assay_version}</td><td>{new Date(run.performed_at).toLocaleString()}</td><td>{run.protocol_name || "—"}{run.protocol_version ? ` · ${run.protocol_version}` : ""}</td><td><span className="badge">{run.status}</span></td></tr>; })}</RegistryTable></>;
}
