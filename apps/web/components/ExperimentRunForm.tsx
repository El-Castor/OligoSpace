import Link from "next/link";

import { WorkspaceFields } from "@/components/WorkspaceFields";
import type { AssaySummary, WorkspaceChoices } from "@/lib/api";

type FormAction = (formData: FormData) => void | Promise<void>;

export function ExperimentRunForm({ action, assays, choices, assayId, error }: { action: FormAction; assays: AssaySummary[]; choices: WorkspaceChoices; assayId?: string; error?: string }) {
  return (
    <form className="record-form" action={action}>
      {error ? <div className="notice" role="alert">{error}</div> : null}
      <div className="form-grid">
        <label className="field"><span>Assay <strong aria-hidden="true">*</strong></span><select name="assay_id" required defaultValue={assayId ?? ""}><option value="" disabled>Select an assay</option>{assays.map((assay) => <option value={assay.id} key={assay.id}>{assay.public_id} · {assay.name} · v{assay.version}</option>)}</select></label>
        <label className="field"><span>Performed at <strong aria-hidden="true">*</strong></span><input name="performed_at" type="datetime-local" required /></label>
        <WorkspaceFields choices={choices} visibility="private" />
        <label className="field"><span>Protocol name</span><input name="protocol_name" maxLength={240} /></label>
        <label className="field"><span>Protocol version</span><input name="protocol_version" maxLength={120} /></label>
        <label className="field field-wide"><span>Conditions (JSON)</span><textarea name="conditions" rows={4} defaultValue="{}" aria-describedby="conditions-help" /><small id="conditions-help">User-provided experimental conditions; values are not inferred.</small></label>
        <label className="field field-wide"><span>Inputs and lot references (JSON)</span><textarea name="input_metadata" rows={4} defaultValue="{}" aria-describedby="inputs-help" /><small id="inputs-help">Contextual references only. This does not create inventory or OligoLot records.</small></label>
        <label className="field field-wide"><span>Notes</span><textarea name="notes" rows={4} /></label>
      </div>
      <div className="form-actions"><button className="primary-button" type="submit">Record experiment run</button><Link className="secondary-button" href="/experiments">Cancel</Link></div>
    </form>
  );
}
