import Link from "next/link";
import { notFound } from "next/navigation";

import { runAssayPrimer3 } from "@/app/scientific-jobs/actions";
import { PageHeader } from "@/components/PageHeader";
import { Primer3JobSection } from "@/components/Primer3JobSection";
import { RecordDetails, RecordField } from "@/components/RecordDetails";
import {
  apiGet,
  apiGetOptional,
  type AssaySummary,
  type CurrentUser,
  type ExperimentRunSummary,
  type ExperimentType,
  type OligoSummary,
  type PageResult,
  type ScientificJobSummary,
  type TargetSummary,
} from "@/lib/api";
import { formatMetric } from "@/lib/registry-format";

export default async function AssayDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ publicId: string }>;
  searchParams: Promise<{ updated?: string; scientific_job?: string; scientific_error?: string }>;
}) {
  const { publicId } = await params;
  const state = await searchParams;
  const [assay, experimentTypes, oligoPage, targetPage, runPage, user] = await Promise.all([
    apiGetOptional<AssaySummary>(`/registry/assays/${encodeURIComponent(publicId)}`),
    apiGetOptional<ExperimentType[]>("/registry/experiment-types?active_only=false"),
    apiGetOptional<PageResult<OligoSummary>>("/registry/oligos?limit=200"),
    apiGetOptional<PageResult<TargetSummary>>("/registry/targets?limit=200"),
    apiGetOptional<PageResult<ExperimentRunSummary>>("/laboratory/runs?limit=200"),
    apiGet<CurrentUser>("/me"),
  ]);
  if (!assay) notFound();
  const jobPage = await apiGetOptional<PageResult<ScientificJobSummary>>(
    `/scientific-jobs?assay_id=${encodeURIComponent(assay.id)}&limit=50`,
  );
  const method = experimentTypes?.find((item) => item.id === assay.experiment_type_id);
  const target = targetPage?.items.find((item) => item.id === assay.target_id);
  const oligos = new Map(oligoPage?.items.map((item) => [item.id, item]));
  const runs = (runPage?.items ?? []).filter((run) => run.assay_id === assay.id);
  const pairChoices = {
    forward: assay.oligos
      .filter((association) => association.role === "forward_primer")
      .flatMap((association) => {
        const oligo = oligos.get(association.oligo_id);
        return oligo ? [{ id: oligo.id, label: `${oligo.public_id} · ${oligo.name} · 5′-${oligo.normalized_sequence}-3′` }] : [];
      }),
    reverse: assay.oligos
      .filter((association) => association.role === "reverse_primer")
      .flatMap((association) => {
        const oligo = oligos.get(association.oligo_id);
        return oligo ? [{ id: oligo.id, label: `${oligo.public_id} · ${oligo.name} · 5′-${oligo.normalized_sequence}-3′` }] : [];
      }),
  };
  const action = runAssayPrimer3.bind(null, assay.public_id);
  return (
    <>
      <PageHeader
        eyebrow={`Assays / ${assay.public_id}`}
        title={assay.name}
        description="Reusable experimental design. Validation belongs to experiment evidence and is not inferred from this definition."
        action={<div className="header-actions"><Link className="secondary-button" href={`/experiments/new?assay=${assay.public_id}`}>Record run</Link><Link className="primary-button" href={`/assays/${assay.public_id}/edit`}>Edit assay</Link></div>}
      />
      {state.updated ? <div className="success-notice" role="status">Assay saved as version {assay.version}; the update was audited.</div> : null}
      {state.scientific_job ? <div className="success-notice" role="status">Scientific job {state.scientific_job} was persisted and queued.</div> : null}
      {state.scientific_error ? <div className="notice" role="alert">{state.scientific_error}</div> : null}
      <RecordDetails>
        <RecordField label="Public ID">{assay.public_id}</RecordField>
        <RecordField label="Status"><span className="badge">{assay.status}</span></RecordField>
        <RecordField label="Method">{method?.name ?? "Unknown catalog entry"}</RecordField>
        <RecordField label="Version">v{assay.version}</RecordField>
        <RecordField label="Target">{target ? <Link className="text-link" href={`/targets/${target.public_id}`}>{target.public_id} · {target.name}</Link> : "Not specified"}</RecordField>
        <RecordField label="Visibility">{assay.visibility}</RecordField>
        <RecordField label="Expected amplicon">{formatMetric(assay.expected_amplicon_length, "bp")}</RecordField>
        <RecordField label="Annealing temperature">{formatMetric(assay.recommended_annealing_temperature_c, "°C")}</RecordField>
        <RecordField label="Expected product" wide>{assay.expected_product || "—"}</RecordField>
        <RecordField label="Protocol notes" wide>{assay.protocol_notes || "—"}</RecordField>
      </RecordDetails>
      <section className="association-card">
        <h2>Oligos and roles</h2>
        {assay.oligos.length ? <div className="association-list">{assay.oligos.map((association) => { const oligo = oligos.get(association.oligo_id); return <div className="association-item" key={`${association.oligo_id}-${association.role}`}><span className="badge">{association.role.replaceAll("_", " ")}</span>{oligo ? <Link href={`/oligos/${oligo.public_id}`}><strong>{oligo.public_id}</strong> · {oligo.name}<small className="sequence">{oligo.normalized_sequence}</small></Link> : <span>Inaccessible oligo</span>}{association.label ? <small>{association.label}</small> : null}</div>; })}</div> : <div className="empty"><strong>No oligos associated</strong>Add contextual oligo roles to make this assay reusable.</div>}
      </section>
      <Primer3JobSection
        title="Forward/Reverse pair analysis"
        description="The unique Forward and Reverse role members are analyzed as stored 5′→3′ sequences. No reverse-complement transformation or compatibility conclusion is inferred."
        action={user.role === "viewer" ? undefined : action}
        jobs={jobPage?.items ?? []}
        currentVersion={assay.version}
        pairChoices={pairChoices}
      />
      <section className="association-card">
        <div className="section-heading"><h2>Experiment history</h2><Link className="text-link" href={`/experiments/new?assay=${assay.public_id}`}>Record a run</Link></div>
        {runs.length ? <div className="association-list">{runs.map((run) => <div className="association-item" key={run.public_id}><span className="badge">v{run.assay_version}</span><Link href={`/experiments/${run.public_id}`}><strong>{run.public_id}</strong> · {new Date(run.performed_at).toLocaleString()}</Link><small>{run.protocol_name || "No protocol name"}</small></div>)}</div> : <div className="empty"><strong>No experiment runs</strong>The assay definition has no execution evidence yet.</div>}
      </section>
    </>
  );
}
