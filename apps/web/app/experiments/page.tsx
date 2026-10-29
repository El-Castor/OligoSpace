import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { RegistryTable } from "@/components/RegistryTable";
import { apiGetOptional, type AssaySummary, type ExperimentRunSummary, type PageResult } from "@/lib/api";

export default async function ExperimentsPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const query = (await searchParams).q?.trim() ?? "";
  const [result, assayPage] = await Promise.all([
    apiGetOptional<PageResult<ExperimentRunSummary>>(`/laboratory/runs${query ? `?q=${encodeURIComponent(query)}` : ""}`),
    apiGetOptional<PageResult<AssaySummary>>("/registry/assays?limit=200"),
  ]);
  const assays = new Map(assayPage?.items.map((assay) => [assay.id, assay]));
  const items = result?.items ?? [];
  return <><PageHeader eyebrow="Research / evidence" title="Experiment runs" description="Repeatable executions of versioned assays. Conditions and observations are user-provided evidence, never changes to the assay definition." action={<Link className="primary-button" href="/experiments/new">New experiment run</Link>} /><RegistrySearch action="/experiments" query={query} />{!result ? <div className="notice">Experiment evidence API unavailable.</div> : null}<RegistryTable count={result?.total ?? 0} columns={["ID", "Assay version", "Performed", "Protocol", "Status"]}>{items.map((run) => { const assay = assays.get(run.assay_id); return <tr key={run.id}><td className="public-id"><Link href={`/experiments/${run.public_id}`}>{run.public_id}</Link></td><td>{assay?.name ?? "Accessible assay"} · v{run.assay_version}</td><td>{new Date(run.performed_at).toLocaleString()}</td><td>{run.protocol_name || "—"}{run.protocol_version ? ` · ${run.protocol_version}` : ""}</td><td><span className="badge">{run.status}</span></td></tr>; })}</RegistryTable></>;
}
