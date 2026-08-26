import { PageHeader } from "@/components/PageHeader";
import { RegistryTable } from "@/components/RegistryTable";
import { apiGetOptional, type PageResult, type TargetSummary } from "@/lib/api";

export default async function TargetsPage() {
  const result = await apiGetOptional<PageResult<TargetSummary>>("/registry/targets");
  const items = result?.items ?? [];
  return (
    <>
      <PageHeader eyebrow="Research / biology" title="Targets" description="Genes, transcripts, loci, and reference sequences that anchor assays and exact oligo mappings." action={<button className="primary-button" type="button" disabled title="Create workflow is the next registry increment">New target</button>} />
      {!result ? <div className="notice">API unavailable. No target annotation or coordinates are inferred.</div> : null}
      <RegistryTable count={result?.total ?? 0} columns={["ID", "Target", "Type", "Gene ID", "Status"]}>
        {items.map((target) => <tr key={target.id}><td className="public-id">{target.public_id}</td><td>{target.name}</td><td>{target.target_type}</td><td>{target.gene_identifier ?? "—"}</td><td><span className="badge">{target.status}</span></td></tr>)}
      </RegistryTable>
    </>
  );
}
