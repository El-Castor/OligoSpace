import { ScientificForm } from "@/components/ScientificForm";
import { FormSection } from "@/components/FormSection";
import { SubmitButton } from "@/components/SubmitButton";
import Link from "next/link";

import { WorkspaceFields } from "@/components/WorkspaceFields";
import type { Organism, TargetSummary, WorkspaceChoices } from "@/lib/api";

type FormAction = (formData: FormData) => void | Promise<void>;

export function TargetForm({ action, organisms, choices, target, error }: { action: FormAction; organisms: Organism[]; choices: WorkspaceChoices; target?: TargetSummary; error?: string }) {
  return (
    <ScientificForm action={action} error={error}>
      <FormSection title="Biological identity" description="Known identifiers and governed reference sequence only.">
        <label className="field"><span>Name <strong aria-hidden="true">*</strong></span><input name="name" required maxLength={240} defaultValue={target?.name} /></label>
        <label className="field"><span>Target type</span><select name="target_type" defaultValue={target?.target_type ?? "gene"}><option value="gene">Gene</option><option value="transcript">Transcript</option><option value="locus">Locus</option><option value="region">Region</option><option value="other">Other</option></select></label>
        <label className="field"><span>Organism</span><select name="organism_id" defaultValue={target?.organism_id ?? ""}><option value="">Not specified</option>{organisms.map((organism) => <option value={organism.id} key={organism.id}>{organism.scientific_name}{organism.common_name ? ` · ${organism.common_name}` : ""}</option>)}</select></label>
        <label className="field"><span>Gene identifier</span><input name="gene_identifier" maxLength={160} defaultValue={target?.gene_identifier ?? ""} /></label>
        <label className="field"><span>Transcript identifier</span><input name="transcript_identifier" maxLength={160} defaultValue={target?.transcript_identifier ?? ""} /></label>

        </FormSection>
      <FormSection title="Reference and annotation" description="Only known reference data; no mapping is inferred."><label className="field field-wide"><span>Description</span><textarea name="description" rows={3} defaultValue={target?.description ?? ""} /></label>
        <label className="field field-wide"><span>Reference sequence</span><textarea className="sequence-input" name="reference_sequence" rows={5} defaultValue={target?.reference_sequence ?? ""} /><small>Only a governed, known reference sequence should be entered. No coordinates are inferred from this field.</small></label>
</FormSection>
      <FormSection title="Access and lifecycle">        <WorkspaceFields choices={choices} visibility={target?.visibility} teamId={target?.owner_team_id} projectId={target?.owner_project_id} />
        {target ? <label className="field"><span>Status</span><select name="status" defaultValue={target.status}><option value="active">Active</option><option value="deprecated">Deprecated</option><option value="archived">Archived</option></select></label> : null}
      </FormSection>
      <div className="form-actions"><SubmitButton>{target ? "Save changes" : "Register target"}</SubmitButton><Link className="secondary-button" href={target ? `/targets/${target.public_id}` : "/targets"}>Cancel</Link></div>
    </ScientificForm>
  );
}
