import Link from "next/link";
import { CopyValue } from "@/components/CopyValue";
import { Primer3Result } from "@/components/Primer3Result";
import type { ScientificJobSummary } from "@/lib/api";
import { jobInputSequences, jobStateDescription } from "@/lib/scientific-presentation";

function JobTime({ value }: { value: string | null }) {
  return value ? <time dateTime={value} title={value}>{new Date(value).toLocaleString()}</time> : <>—</>;
}

export function ScientificJobCard({ job, currentVersion }: { job: ScientificJobSummary; currentVersion?: number }) {
  const sequences = jobInputSequences(job.input_snapshot);
  return <article className="scientific-job" aria-labelledby={`job-${job.public_id}`}>
    <header className="job-header"><div><h3 id={`job-${job.public_id}`}><Link className="text-link" href={`/scientific-jobs/${job.public_id}`}>{job.public_id}</Link></h3><p className="job-description">{jobStateDescription(job.state)}</p></div><div className="job-header-actions"><CopyValue value={job.public_id} label={`Copy ${job.public_id}`} /><span className="badge job-state" data-state={job.state} role="status" aria-label={`Execution state: ${job.state}`}>{job.state}</span></div></header>
    <dl className="job-times"><div><dt>Queued</dt><dd><JobTime value={job.queued_at} /></dd></div><div><dt>Started</dt><dd><JobTime value={job.started_at} /></dd></div><div><dt>Completed</dt><dd><JobTime value={job.completed_at} /></dd></div></dl>
    {currentVersion && job.assay_version !== currentVersion ? <div className="notice">This result belongs to Assay version {job.assay_version}; the current version is {currentVersion}.</div> : null}
    {job.last_error_summary ? <div className="notice" role="alert">{job.last_error_code}: {job.last_error_summary}</div> : null}
    {sequences.length ? <section className="job-inputs" aria-label="Persisted sequence inputs">{sequences.map((input) => <div key={input.label}><span className="job-input-label">{input.label}{input.publicId ? ` · ${input.publicId}` : ""}</span><code className="job-sequence">{input.sequence}</code><CopyValue value={input.sequence} label={`Copy ${input.publicId ?? input.label} input sequence`} /></div>)}</section> : null}
    <Primer3Result job={job} />
    {job.result ? <div className="job-result-actions"><CopyValue value={JSON.stringify(job.result.payload, null, 2)} label="Copy Primer3 result JSON" /><span>Stored thermodynamic facts; no experimental validation inferred.</span></div> : <p className={job.state === "succeeded" ? "notice" : "job-description"}>No persisted result available for this job.</p>}
    {job.attempts.length ? <details className="job-attempts"><summary>Execution attempts ({job.attempts.length})</summary><div className="table-scroll" role="region" aria-label={`${job.public_id} execution attempts`} tabIndex={0}><table><thead><tr><th scope="col">Attempt</th><th scope="col">State</th><th scope="col">Started</th><th scope="col">Completed</th><th scope="col">Error</th></tr></thead><tbody>{job.attempts.map((attempt) => <tr key={attempt.id}><td>{attempt.attempt_number}</td><td>{attempt.state}</td><td><JobTime value={attempt.started_at} /></td><td><JobTime value={attempt.completed_at} /></td><td>{attempt.error_code ?? "—"}{attempt.error_summary ? ` · ${attempt.error_summary}` : ""}</td></tr>)}</tbody></table></div></details> : null}
    <details><summary>Parameters and provenance</summary><pre>{JSON.stringify({
      input_sha256: job.input_sha256,
      input_snapshot: job.input_snapshot,
      requested_parameters: job.requested_parameters,
      parameters: job.effective_parameters,
      attempts: job.attempts,
      result: job.result ? {
        result_schema_version: job.result.result_schema_version, algorithm: job.result.algorithm,
        started_at: job.result.started_at, completed_at: job.result.completed_at,
        tool_version: job.result.tool_version, tool_source_sha256: job.result.tool_source_sha256,
        worker_version: job.result.worker_version, wrapper_contract_version: job.result.wrapper_contract_version,
        build_identity: job.result.build_identity, executed_at: job.result.executed_at,
      } : null,
    }, null, 2)}</pre></details>
    {job.result ? <details><summary>Stored result JSON</summary><pre>{JSON.stringify(job.result.payload, null, 2)}</pre></details> : null}
  </article>;
}
