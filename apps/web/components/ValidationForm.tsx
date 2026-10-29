import Link from "next/link";

import type { AssaySummary, ExperimentRunSummary, ExperimentType, ValidationSummary } from "@/lib/api";

type FormAction = (formData: FormData) => void | Promise<void>;

export function ValidationForm({ action, assays, runs, experimentTypes, assayId, runId, supersedes, error }: { action: FormAction; assays: AssaySummary[]; runs: ExperimentRunSummary[]; experimentTypes: ExperimentType[]; assayId?: string; runId?: string; supersedes?: ValidationSummary; error?: string }) {
  const selectedAssay = assays.find((assay) => assay.id === assayId);
  const experimentType = experimentTypes.find((item) => item.id === selectedAssay?.experiment_type_id);
  const hints = experimentType?.recommended_validation_fields ?? {};
  return (
    <form className="record-form" action={action}>
      {error ? <div className="notice" role="alert">{error}</div> : null}
      {supersedes ? <div className="notice">This new evidence will explicitly supersede {supersedes.public_id}; the prior conclusion and files remain retained.</div> : null}
      <input type="hidden" name="supersedes_validation_public_id" value={supersedes?.public_id ?? ""} />
      <div className="form-grid">
        <label className="field"><span>Assay <strong aria-hidden="true">*</strong></span><select name="assay_id" required defaultValue={assayId ?? ""}><option value="" disabled>Select an assay</option>{assays.map((assay) => <option value={assay.id} key={assay.id}>{assay.public_id} · {assay.name}</option>)}</select></label>
        <label className="field"><span>Experiment run</span><select name="experiment_run_id" defaultValue={runId ?? ""}><option value="">Assay-level validation</option>{runs.map((run) => <option value={run.id} key={run.id}>{run.public_id} · {new Date(run.performed_at).toLocaleString()}</option>)}</select></label>
        <label className="field"><span>Result <strong aria-hidden="true">*</strong></span><select name="status" required defaultValue="inconclusive"><option value="pending">Pending</option><option value="passed">Passed</option><option value="failed">Failed</option><option value="inconclusive">Inconclusive</option></select></label>
        <label className="field"><span>Validated at <strong aria-hidden="true">*</strong></span><input name="validated_at" type="datetime-local" required /></label>
        <label className="field field-wide"><span>Conclusion <strong aria-hidden="true">*</strong></span><textarea name="conclusion" rows={4} required maxLength={10000} /></label>
        <label className="field field-wide"><span>Measurements (JSON)</span><textarea name="measurements" rows={5} defaultValue="{}" /><small>Method guidance: {Object.keys(hints).length ? JSON.stringify(hints) : "No configured fields. Measurements remain user-provided."}</small></label>
        <label className="field field-wide"><span>Notes</span><textarea name="notes" rows={4} /></label>
      </div>
      <div className="form-actions"><button className="primary-button" type="submit">Record validation evidence</button><Link className="secondary-button" href="/validation">Cancel</Link></div>
    </form>
  );
}
