import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { RegistryTable } from "@/components/RegistryTable";
import { apiGetOptional, type AssaySummary, type PageResult } from "@/lib/api";
import { formatMetric } from "@/lib/registry-format";

export default async function AssaysPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const query = (await searchParams).q?.trim() ?? "";
  const result = await apiGetOptional<PageResult<AssaySummary>>(`/registry/assays${query ? `?q=${encodeURIComponent(query)}` : ""}`);
  const items = result?.items ?? [];
  return (
    <>
      <PageHeader eyebrow="Research / designs" title="Assays" description="Reusable experimental designs where oligo direction, target, method, and expected product gain their context." action={<Link className="primary-button" href="/assays/new">New assay</Link>} />
      <RegistrySearch action="/assays" query={query} />
      {!result ? <div className="notice">API unavailable. Assay validation is never assumed.</div> : null}
      <RegistryTable count={result?.total ?? 0} columns={["ID", "Assay", "Expected amplicon", "Version", "Status"]}>
        {items.map((assay) => <tr key={assay.id}><td className="public-id"><Link href={`/assays/${assay.public_id}`}>{assay.public_id}</Link></td><td><Link className="row-link" href={`/assays/${assay.public_id}`}>{assay.name}</Link></td><td>{formatMetric(assay.expected_amplicon_length, "bp")}</td><td>v{assay.version}</td><td><span className="badge">{assay.status}</span></td></tr>)}
      </RegistryTable>
    </>
  );
}
