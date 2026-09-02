import Link from "next/link";

import { WorkspaceFields } from "@/components/WorkspaceFields";
import type { OligoSummary, WorkspaceChoices } from "@/lib/api";

type FormAction = (formData: FormData) => void | Promise<void>;

export function OligoForm({ action, choices, oligo, error }: { action: FormAction; choices: WorkspaceChoices; oligo?: OligoSummary; error?: string }) {
  return (
    <form className="record-form" action={action}>
      {error ? <div className="notice" role="alert">{error}</div> : null}
      <div className="form-grid">
        <label className="field"><span>Name <strong aria-hidden="true">*</strong></span><input name="name" required maxLength={240} defaultValue={oligo?.name} /></label>
        <label className="field"><span>Oligo type</span><select name="oligo_type" defaultValue={oligo?.oligo_type ?? "DNA"}><option>DNA</option><option>RNA</option><option>Modified DNA</option><option>Modified RNA</option></select></label>
        <label className="field field-wide"><span>Sequence 5′→3′ <strong aria-hidden="true">*</strong></span><textarea className="sequence-input" name="sequence" required={!oligo} readOnly={Boolean(oligo)} rows={4} defaultValue={oligo?.normalized_sequence} aria-describedby={oligo ? "sequence-identity-help" : undefined} /></label>
        {oligo ? <p className="field-help field-wide" id="sequence-identity-help">Sequence is immutable because it defines biological identity and calculated provenance. Create a new oligo to register another sequence.</p> : null}
        <label className="field field-wide"><span>Description</span><textarea name="description" rows={3} defaultValue={oligo?.description ?? ""} /></label>
        <label className="field field-wide"><span>Notes</span><textarea name="notes" rows={3} defaultValue={oligo?.notes ?? ""} /></label>
        <WorkspaceFields choices={choices} visibility={oligo?.visibility} teamId={oligo?.owner_team_id} projectId={oligo?.owner_project_id} />
        {oligo ? <label className="field"><span>Status</span><select name="status" defaultValue={oligo.status}><option value="active">Active</option><option value="deprecated">Deprecated</option><option value="archived">Archived</option></select></label> : null}
      </div>
      <div className="form-actions"><button className="primary-button" type="submit">{oligo ? "Save changes" : "Register oligo"}</button><Link className="secondary-button" href={oligo ? `/oligos/${oligo.public_id}` : "/oligos"}>Cancel</Link></div>
    </form>
  );
}
