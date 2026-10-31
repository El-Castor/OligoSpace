import Link from "next/link";

import { registryData } from "@/lib/registry-data";
import { registryOffset } from "@/lib/registry-page";
import { ScientificValue } from "@/components/ScientificValue";
import { PageHeader } from "@/components/PageHeader";
import { RegistrySearch } from "@/components/RegistrySearch";
import { RegistryTable } from "@/components/RegistryTable";
import { type PageResult, type ValidationSummary } from "@/lib/api";

export default async function ValidationPage({ searchParams }: { searchParams: Promise<{ q?: string; offset?: string }> }) {
  const params = await searchParams;
  const query = params.q?.trim() ?? "";
  const offset = registryOffset(params.offset);
  const { result, error } = await registryData<PageResult<ValidationSummary>>(`/laboratory/validations?q=${encodeURIComponent(query)}&offset=${offset}`);
  const items = result?.items ?? [];
  return <><PageHeader eyebrow="Lab / evidence" title="Validation" description="Explicit contextual conclusions for an assay or experiment run. Inconclusive and superseded evidence remains visible." action={<Link className="primary-button" href="/validation/new">New validation</Link>} /><RegistrySearch action="/validation" query={query} /><RegistryTable shown={items.length} label="Validation" query={query} path="/validation" offset={result?.offset ?? offset} limit={result?.limit ?? 50} error={error} count={result?.total ?? 0} columns={["ID", "Result", "Conclusion", "Context", "Validated"]}>{items.map((validation) => <tr key={validation.id}><td className="public-id"><ScientificValue value={validation.public_id} href={`/validation/${validation.public_id}`} copy /></td><td><span className="badge">{validation.status}</span></td><td><ScientificValue value={validation.conclusion} href={`/validation/${validation.public_id}`} /></td><td>{validation.experiment_run_id ? "Experiment run" : "Assay"}</td><td>{new Date(validation.validated_at).toLocaleString()}</td></tr>)}</RegistryTable></>;
}
