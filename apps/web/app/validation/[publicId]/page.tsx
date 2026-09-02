import Link from "next/link";
import { notFound } from "next/navigation";

import { uploadValidationAttachment } from "@/app/validation/actions";
import { AttachmentList } from "@/components/AttachmentList";
import { AttachmentUploadForm } from "@/components/AttachmentUploadForm";
import { PageHeader } from "@/components/PageHeader";
import { RecordDetails, RecordField } from "@/components/RecordDetails";
import { apiGetOptional, type AssaySummary, type ExperimentRunSummary, type PageResult, type ValidationDetail } from "@/lib/api";

export default async function ValidationDetailPage({ params, searchParams }: { params: Promise<{ publicId: string }>; searchParams: Promise<{ attachment?: string; attachmentError?: string }> }) {
  const { publicId } = await params;
  const state = await searchParams;
  const [validation, assays, runs] = await Promise.all([apiGetOptional<ValidationDetail>(`/laboratory/validations/${encodeURIComponent(publicId)}`), apiGetOptional<PageResult<AssaySummary>>("/registry/assays?limit=200"), apiGetOptional<PageResult<ExperimentRunSummary>>("/laboratory/runs?limit=200")]);
  if (!validation) notFound();
  const assay = assays?.items.find((item) => item.id === validation.assay_id);
  const run = runs?.items.find((item) => item.id === validation.experiment_run_id);
  const attachmentAction = uploadValidationAttachment.bind(null, validation.public_id);
  return <><PageHeader eyebrow={`Validation / ${validation.public_id}`} title={validation.conclusion} description="User-recorded contextual evidence. Status and measurements are explicit; no global oligo validation is inferred." action={validation.status !== "superseded" ? <Link className="primary-button" href={`/validation/new?assay=${assay?.public_id ?? ""}&run=${run?.public_id ?? ""}&supersedes=${validation.public_id}`}>Supersede with new evidence</Link> : undefined} /><RecordDetails><RecordField label="Public ID">{validation.public_id}</RecordField><RecordField label="Result"><span className="badge">{validation.status}</span></RecordField><RecordField label="Assay">{assay ? <Link className="text-link" href={`/assays/${assay.public_id}`}>{assay.public_id} · {assay.name}</Link> : "Inaccessible assay"}</RecordField><RecordField label="Run">{run ? <Link className="text-link" href={`/experiments/${run.public_id}`}>{run.public_id}</Link> : "Assay-level evidence"}</RecordField><RecordField label="Validated at">{new Date(validation.validated_at).toLocaleString()}</RecordField><RecordField label="Validator ID">{validation.validated_by_id}</RecordField><RecordField label="Measurements" wide><pre>{JSON.stringify(validation.measurements, null, 2)}</pre></RecordField><RecordField label="Notes" wide>{validation.notes || "—"}</RecordField></RecordDetails><section className="association-card" id="evidence-files"><h2>Validation evidence files</h2>{state.attachment ? <div className="success-notice" role="status">Evidence stored privately in quarantine.</div> : null}<AttachmentList attachments={validation.attachments} /><AttachmentUploadForm action={attachmentAction} error={state.attachmentError} /></section></>;
}
