import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { RegistryTable } from "@/components/RegistryTable";
import { apiGetOptional, type PageResult, type ValidationSummary } from "@/lib/api";

export default async function ValidationPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const query = (await searchParams).q?.trim() ?? "";
  const result = await apiGetOptional<PageResult<ValidationSummary>>(`/laboratory/validations${query ? `?q=${encodeURIComponent(query)}` : ""}`);
  const items = result?.items ?? [];
  return <><PageHeader eyebrow="Lab / evidence" title="Validation" description="Explicit contextual conclusions for an assay or experiment run. Inconclusive and superseded evidence remains visible." action={<Link className="primary-button" href="/validation/new">New validation</Link>} /><RegistrySearch action="/validation" query={query} /><RegistryTable count={result?.total ?? 0} columns={["ID", "Result", "Conclusion", "Context", "Validated"]}>{items.map((validation) => <tr key={validation.id}><td className="public-id"><Link href={`/validation/${validation.public_id}`}>{validation.public_id}</Link></td><td><span className="badge">{validation.status}</span></td><td><Link className="row-link" href={`/validation/${validation.public_id}`}>{validation.conclusion}</Link></td><td>{validation.experiment_run_id ? "Experiment run" : "Assay"}</td><td>{new Date(validation.validated_at).toLocaleString()}</td></tr>)}</RegistryTable></>;
}
