import Link from "next/link";

import type { AssaySummary, ExperimentType, OligoSummary, TargetSummary } from "@/lib/api";

type FormAction = (formData: FormData) => void | Promise<void>;

const roles = [
  ["forward_primer", "Forward primer"], ["reverse_primer", "Reverse primer"],
  ["probe", "Probe"], ["internal_oligo", "Internal oligo"],
  ["sequencing_primer", "Sequencing primer"], ["adapter", "Adapter"],
  ["guide", "Guide"], ["donor", "Donor"], ["template", "Template"], ["other", "Other"],
] as const;

export function AssayForm({ action, experimentTypes, oligos, targets, assay, error }: { action: FormAction; experimentTypes: ExperimentType[]; oligos: OligoSummary[]; targets: TargetSummary[]; assay?: AssaySummary; error?: string }) {
  const associations = Array.from({ length: Math.max(3, assay?.oligos.length ?? 0) }, (_, index) => assay?.oligos[index]);
  return (
    <form className="record-form" action={action}>
      {error ? <div className="notice" role="alert">{error}</div> : null}
      <div className="form-grid">
        <label className="field"><span>Name <strong aria-hidden="true">*</strong></span><input name="name" required maxLength={240} defaultValue={assay?.name} /></label>
        <label className="field"><span>Experiment type <strong aria-hidden="true">*</strong></span><select name="experiment_type_id" required defaultValue={assay?.experiment_type_id ?? ""}><option value="" disabled>Select a method</option>{experimentTypes.map((type) => <option value={type.id} key={type.id}>{type.name}</option>)}</select></label>
        <label className="field"><span>Target</span><select name="target_id" defaultValue={assay?.target_id ?? ""}><option value="">No target selected</option>{targets.map((target) => <option value={target.id} key={target.id}>{target.public_id} · {target.name}</option>)}</select></label>
        <label className="field"><span>Visibility</span><select name="visibility" defaultValue={assay?.visibility ?? "team"}><option value="private">Private</option><option value="team">Team</option><option value="organization">Institute</option></select></label>
        <label className="field"><span>Expected amplicon length (bp)</span><input name="expected_amplicon_length" type="number" min="1" defaultValue={assay?.expected_amplicon_length ?? ""} /></label>
        <label className="field"><span>Annealing temperature (°C)</span><input name="recommended_annealing_temperature_c" type="number" step="0.1" defaultValue={assay?.recommended_annealing_temperature_c ?? ""} /></label>
        <label className="field field-wide"><span>Expected product</span><textarea name="expected_product" rows={2} defaultValue={assay?.expected_product ?? ""} /></label>
        <fieldset className="association-fieldset field-wide"><legend>Oligos and contextual roles</legend><p>Select only roles allowed by the chosen experiment type. Oligo identity remains separate from its assay role.</p>{associations.map((association, index) => <div className="association-row" key={`${association?.oligo_id ?? "new"}-${index}`}><label><span>Oligo {index + 1}</span><select name="oligo_id" defaultValue={association?.oligo_id ?? ""}><option value="">None</option>{oligos.map((oligo) => <option value={oligo.id} key={oligo.id}>{oligo.public_id} · {oligo.name}</option>)}</select></label><label><span>Role</span><select name="role" defaultValue={association?.role ?? ""}><option value="">Select role</option>{roles.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label><label><span>Label</span><input name="label" maxLength={120} defaultValue={association?.label ?? ""} /></label></div>)}</fieldset>
        <label className="field field-wide"><span>Protocol notes</span><textarea name="protocol_notes" rows={4} defaultValue={assay?.protocol_notes ?? ""} /></label>
        {assay ? <label className="field"><span>Status</span><select name="status" defaultValue={assay.status}><option value="active">Active</option><option value="deprecated">Deprecated</option><option value="archived">Archived</option></select></label> : null}
      </div>
      <div className="form-actions"><button className="primary-button" type="submit">{assay ? "Save as new version" : "Register assay"}</button><Link className="secondary-button" href={assay ? `/assays/${assay.public_id}` : "/assays"}>Cancel</Link></div>
    </form>
  );
}
