import Link from "next/link";

import type { Organism, TargetSummary } from "@/lib/api";

type FormAction = (formData: FormData) => void | Promise<void>;

export function TargetForm({ action, organisms, target, error }: { action: FormAction; organisms: Organism[]; target?: TargetSummary; error?: string }) {
  return (
    <form className="record-form" action={action}>
      {error ? <div className="notice" role="alert">{error}</div> : null}
      <div className="form-grid">
        <label className="field"><span>Name <strong aria-hidden="true">*</strong></span><input name="name" required maxLength={240} defaultValue={target?.name} /></label>
        <label className="field"><span>Target type</span><select name="target_type" defaultValue={target?.target_type ?? "gene"}><option value="gene">Gene</option><option value="transcript">Transcript</option><option value="locus">Locus</option><option value="region">Region</option><option value="other">Other</option></select></label>
        <label className="field"><span>Organism</span><select name="organism_id" defaultValue={target?.organism_id ?? ""}><option value="">Not specified</option>{organisms.map((organism) => <option value={organism.id} key={organism.id}>{organism.scientific_name}{organism.common_name ? ` · ${organism.common_name}` : ""}</option>)}</select></label>
        <label className="field"><span>Gene identifier</span><input name="gene_identifier" maxLength={160} defaultValue={target?.gene_identifier ?? ""} /></label>
        <label className="field"><span>Transcript identifier</span><input name="transcript_identifier" maxLength={160} defaultValue={target?.transcript_identifier ?? ""} /></label>
        <label className="field"><span>Visibility</span><select name="visibility" defaultValue={target?.visibility ?? "team"}><option value="private">Private</option><option value="team">Team</option><option value="organization">Institute</option></select></label>
        <label className="field field-wide"><span>Description</span><textarea name="description" rows={3} defaultValue={target?.description ?? ""} /></label>
        <label className="field field-wide"><span>Reference sequence</span><textarea className="sequence-input" name="reference_sequence" rows={5} defaultValue={target?.reference_sequence ?? ""} /><small>Only a governed, known reference sequence should be entered. No coordinates are inferred from this field.</small></label>
        {target ? <label className="field"><span>Status</span><select name="status" defaultValue={target.status}><option value="active">Active</option><option value="deprecated">Deprecated</option><option value="archived">Archived</option></select></label> : null}
      </div>
      <div className="form-actions"><button className="primary-button" type="submit">{target ? "Save changes" : "Register target"}</button><Link className="secondary-button" href={target ? `/targets/${target.public_id}` : "/targets"}>Cancel</Link></div>
    </form>
  );
}
