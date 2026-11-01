import { SubmitButton } from "@/components/SubmitButton";
import Link from "next/link";

import { ScientificJobAutoRefresh } from "@/components/ScientificJobAutoRefresh";
import type { ScientificJobSummary } from "@/lib/api";

type ComponentFact = {
  state?: string;
  value?: number;
  units?: string;
  method?: string;
  tool_mode?: string;
};

function fact(value: unknown): ComponentFact | null {
  return typeof value === "object" && value !== null ? (value as ComponentFact) : null;
}

function object(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : null;
}

function FactCard({ label, value }: { label: string; value: unknown }) {
  const item = fact(value);
  return (
    <div className="scientific-fact">
      <span>{label}</span>
      {item?.state === "available" ? (
        <strong>
          {Number(item.value).toFixed(2)} {item.units === "degC" ? "°C" : item.units}
        </strong>
      ) : (
        <strong>{item?.state ?? "unavailable"}</strong>
      )}
      <small>
        {item?.method ?? "No method returned"}
        {item?.tool_mode ? ` · ${item.tool_mode}` : ""}
      </small>
    </div>
  );
}

function Result({ job }: { job: ScientificJobSummary }) {
  if (!job.result) return null;
  const payload = job.result.payload;
  if (job.kind === "oligo_primer3_qc") {
    return (
      <div className="scientific-results">
        <FactCard label="Primer3 nearest-neighbor Tm" value={payload.nearest_neighbor_tm} />
        <FactCard label="Hairpin" value={payload.hairpin} />
        <FactCard label="Homodimer" value={payload.homodimer} />
      </div>
    );
  }
  const forward = object(payload.forward);
  const reverse = object(payload.reverse);
  return (
    <>
      <h3>Forward primer</h3>
      <div className="scientific-results">
        <FactCard label="Nearest-neighbor Tm" value={forward?.nearest_neighbor_tm} />
        <FactCard label="Hairpin" value={forward?.hairpin} />
        <FactCard label="Homodimer" value={forward?.homodimer} />
      </div>
      <h3>Reverse primer</h3>
      <div className="scientific-results">
        <FactCard label="Nearest-neighbor Tm" value={reverse?.nearest_neighbor_tm} />
        <FactCard label="Hairpin" value={reverse?.hairpin} />
        <FactCard label="Homodimer" value={reverse?.homodimer} />
      </div>
      <h3>Pair facts</h3>
      <div className="scientific-results">
        <FactCard label="Absolute Tm delta" value={payload.tm_delta} />
        <FactCard label="Heterodimer" value={payload.heterodimer} />
        <FactCard label="3′ end complementarity" value={payload.end_complementarity} />
      </div>
    </>
  );
}

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
        <form action={action} className="scientific-parameters">
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
            <article key={job.public_id} className="scientific-job">
              <div className="section-heading">
                <h3><Link className="text-link" href={`/scientific-jobs/${job.public_id}`}>{job.public_id}</Link></h3>
                <span className="badge">{job.state}</span>
              </div>
              {currentVersion && job.assay_version !== currentVersion ? (
                <div className="notice">This result belongs to Assay version {job.assay_version}; the current version is {currentVersion}.</div>
              ) : null}
              {job.last_error_summary ? (
                <div className="notice" role="alert">{job.last_error_code}: {job.last_error_summary}</div>
              ) : null}
              <Result job={job} />
              <details>
                <summary>Parameters and provenance</summary>
                <pre>{JSON.stringify({
                  input_sha256: job.input_sha256,
                  parameters: job.effective_parameters,
                  attempts: job.attempts,
                  result: job.result ? {
                    tool_version: job.result.tool_version,
                    tool_source_sha256: job.result.tool_source_sha256,
                    worker_version: job.result.worker_version,
                    wrapper_contract_version: job.result.wrapper_contract_version,
                    build_identity: job.result.build_identity,
                    executed_at: job.result.executed_at,
                  } : null,
                }, null, 2)}</pre>
              </details>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty compact"><strong>No Primer3 jobs yet</strong>Run a reproducible analysis to persist its facts and provenance.</div>
      )}
    </section>
  );
}
