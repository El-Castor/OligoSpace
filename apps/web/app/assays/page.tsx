import Link from "next/link";

import { registryData } from "@/lib/registry-data";
import { registryOffset } from "@/lib/registry-page";
import { ScientificValue } from "@/components/ScientificValue";
import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { RegistryTable } from "@/components/RegistryTable";
import { type AssaySummary, type PageResult } from "@/lib/api";
import { formatMetric } from "@/lib/registry-format";

export default async function AssaysPage({ searchParams }: { searchParams: Promise<{ q?: string; offset?: string }> }) {
  const params = await searchParams;
  const query = params.q?.trim() ?? "";
  const offset = registryOffset(params.offset);
  const { result, error } = await registryData<PageResult<AssaySummary>>(`/registry/assays?q=${encodeURIComponent(query)}&offset=${offset}`);
  const items = result?.items ?? [];
  return (
    <>
      <PageHeader eyebrow="Research / designs" title="Assays" description="Reusable experimental designs where oligo direction, target, method, and expected product gain their context." action={<Link className="primary-button" href="/assays/new">New assay</Link>} />
      <RegistrySearch action="/assays" query={query} />
      <RegistryTable shown={items.length} label="Assays" query={query} path="/assays" offset={result?.offset ?? offset} limit={result?.limit ?? 50} error={error} count={result?.total ?? 0} columns={["ID", "Assay", "Expected amplicon", "Version", "Status"]}>
        {items.map((assay) => <tr key={assay.id}><td className="public-id"><ScientificValue value={assay.public_id} href={`/assays/${assay.public_id}`} copy /></td><td><ScientificValue value={assay.name} href={`/assays/${assay.public_id}`} /></td><td className="numeric">{formatMetric(assay.expected_amplicon_length, "bp")}</td><td className="numeric">v{assay.version}</td><td><span className="badge">{assay.status}</span></td></tr>)}
      </RegistryTable>
    </>
  );
}
