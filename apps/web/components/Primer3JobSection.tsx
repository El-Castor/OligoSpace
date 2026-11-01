import { SubmitButton } from "@/components/SubmitButton";
import { ScientificJobCard } from "@/components/ScientificJobCard";

import { ScientificJobAutoRefresh } from "@/components/ScientificJobAutoRefresh";
import type { ScientificJobSummary } from "@/lib/api";

export function Primer3JobSection({
  title,
  description,
  action,
  jobs,
  currentVersion,
  pairChoices,
}: {
  title: string;
  description: string;
  action?: (formData: FormData) => Promise<void>;
  jobs: ScientificJobSummary[];
  currentVersion?: number;
  pairChoices?: {
    forward: Array<{ id: string; label: string }>;
    reverse: Array<{ id: string; label: string }>;
  };
}) {
  const active = jobs.some((job) => ["queued", "running", "retrying"].includes(job.state));
  return (
    <section className="provenance-card scientific-job-section">
      <ScientificJobAutoRefresh active={active} />
      <h2>{title}</h2>
      <p>{description}</p>
      {action ? (
        <form action={action} className="scientific-parameters" aria-label="Primer3 parameters">
          {pairChoices ? (
            <>
              <label>
                <span>Forward oligo</span>
                <select name="forward_oligo_id" required defaultValue={pairChoices.forward.length === 1 ? pairChoices.forward[0].id : ""}>
                  <option value="">Select Forward role member</option>
                  {pairChoices.forward.map((choice) => <option key={choice.id} value={choice.id}>{choice.label}</option>)}
                </select>
              </label>
              <label>
                <span>Reverse oligo</span>
                <select name="reverse_oligo_id" required defaultValue={pairChoices.reverse.length === 1 ? pairChoices.reverse[0].id : ""}>
                  <option value="">Select Reverse role member</option>
                  {pairChoices.reverse.map((choice) => <option key={choice.id} value={choice.id}>{choice.label}</option>)}
                </select>
              </label>
            </>
          ) : null}
          <label><span>Monovalent salt</span><input name="mv_conc_mM" type="number" min="0" max="1000" step="0.1" defaultValue="50" /><small>mM</small></label>
          <label><span>Divalent salt</span><input name="dv_conc_mM" type="number" min="0" max="100" step="0.1" defaultValue="1.5" /><small>mM</small></label>
          <label><span>dNTP</span><input name="dntp_conc_mM" type="number" min="0" max="100" step="0.1" defaultValue="0.6" /><small>mM</small></label>
          <label><span>Oligo concentration</span><input name="dna_conc_nM" type="number" min="0.1" max="100000" step="0.1" defaultValue="50" /><small>nM</small></label>
          <label><span>Maximum loop</span><input name="max_loop" type="number" min="0" max="100" defaultValue="30" /><small>nt</small></label>
          <SubmitButton className="primary-button">Run Primer3 analysis</SubmitButton>
        </form>
      ) : null}
      <p className="scientific-disclaimer">
        Thermodynamic facts only; no experimental suitability, amplification efficiency,
        validation, or specificity is inferred.
      </p>
      {jobs.length ? (
        <div className="scientific-jobs">
          {jobs.map((job) => (
            <ScientificJobCard key={job.public_id} job={job} currentVersion={currentVersion} />
          ))}
        </div>
      ) : (
        <div className="empty compact"><strong>No Primer3 jobs yet</strong>Run a reproducible analysis to persist its facts and provenance.</div>
      )}
    </section>
  );
}
