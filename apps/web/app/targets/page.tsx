import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { RegistryTable } from "@/components/RegistryTable";
import { apiGetOptional, type PageResult, type TargetSummary } from "@/lib/api";

export default async function TargetsPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const query = (await searchParams).q?.trim() ?? "";
  const result = await apiGetOptional<PageResult<TargetSummary>>(`/registry/targets${query ? `?q=${encodeURIComponent(query)}` : ""}`);
  const items = result?.items ?? [];
  return (
    <>
      <PageHeader eyebrow="Research / biology" title="Targets" description="Genes, transcripts, loci, and reference sequences that anchor assays and exact oligo mappings." action={<Link className="primary-button" href="/targets/new">New target</Link>} />
      <RegistrySearch action="/targets" query={query} />
      {!result ? <div className="notice">API unavailable. No target annotation or coordinates are inferred.</div> : null}
      <RegistryTable count={result?.total ?? 0} columns={["ID", "Target", "Type", "Gene ID", "Status"]}>
        {items.map((target) => <tr key={target.id}><td className="public-id"><Link href={`/targets/${target.public_id}`}>{target.public_id}</Link></td><td><Link className="row-link" href={`/targets/${target.public_id}`}>{target.name}</Link></td><td>{target.target_type}</td><td>{target.gene_identifier ?? "—"}</td><td><span className="badge">{target.status}</span></td></tr>)}
      </RegistryTable>
    </>
  );
}
