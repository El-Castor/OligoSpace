import Link from "next/link";

import { registryData } from "@/lib/registry-data";
import { registryOffset } from "@/lib/registry-page";
import { ScientificValue } from "@/components/ScientificValue";
import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { RegistryTable } from "@/components/RegistryTable";
import { type PageResult, type TargetSummary } from "@/lib/api";

export default async function TargetsPage({ searchParams }: { searchParams: Promise<{ q?: string; offset?: string }> }) {
  const params = await searchParams;
  const query = params.q?.trim() ?? "";
  const offset = registryOffset(params.offset);
  const { result, error } = await registryData<PageResult<TargetSummary>>(`/registry/targets?q=${encodeURIComponent(query)}&offset=${offset}`);
  const items = result?.items ?? [];
  return (
    <>
      <PageHeader eyebrow="Research / biology" title="Targets" description="Genes, transcripts, loci, and reference sequences that anchor assays and exact oligo mappings." action={<Link className="primary-button" href="/targets/new">New target</Link>} />
      <RegistrySearch action="/targets" query={query} />
      <RegistryTable shown={items.length} label="Targets" query={query} path="/targets" offset={result?.offset ?? offset} limit={result?.limit ?? 50} error={error} count={result?.total ?? 0} columns={["ID", "Target", "Type", "Gene ID", "Status"]}>
        {items.map((target) => <tr key={target.id}><td className="public-id"><ScientificValue value={target.public_id} href={`/targets/${target.public_id}`} copy /></td><td><ScientificValue value={target.name} href={`/targets/${target.public_id}`} /></td><td>{target.target_type}</td><td><ScientificValue value={target.gene_identifier ?? "—"} /></td><td><span className="badge">{target.status}</span></td></tr>)}
      </RegistryTable>
    </>
  );
}
