import { PageHeader } from "@/components/PageHeader";
import { RegistryTable } from "@/components/RegistryTable";
import { apiGetOptional, type AssaySummary, type PageResult } from "@/lib/api";
import { formatMetric } from "@/lib/registry-format";

export default async function AssaysPage() {
  const result = await apiGetOptional<PageResult<AssaySummary>>("/registry/assays");
  const items = result?.items ?? [];
  return (
    <>
      <PageHeader eyebrow="Research / designs" title="Assays" description="Reusable experimental designs where oligo direction, target, method, and expected product gain their context." action={<button className="primary-button" type="button" disabled title="Create workflow is the next registry increment">New assay</button>} />
      {!result ? <div className="notice">API unavailable. Assay validation is never assumed.</div> : null}
      <RegistryTable count={result?.total ?? 0} columns={["ID", "Assay", "Expected amplicon", "Version", "Status"]}>
        {items.map((assay) => <tr key={assay.id}><td className="public-id">{assay.public_id}</td><td>{assay.name}</td><td>{formatMetric(assay.expected_amplicon_length, "bp")}</td><td>v{assay.version}</td><td><span className="badge">{assay.status}</span></td></tr>)}
      </RegistryTable>
    </>
  );
}
