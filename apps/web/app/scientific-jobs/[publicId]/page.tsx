import { notFound } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { Primer3JobSection } from "@/components/Primer3JobSection";
import { apiGet, ApiError, type ScientificJobSummary } from "@/lib/api";
import Link from "next/link";
import { jobSourceHref } from "@/lib/scientific-presentation";

export default async function ScientificJobDetailPage({ params }: { params: Promise<{ publicId: string }> }) {
  const { publicId } = await params;
  let job: ScientificJobSummary;
  try { job = await apiGet<ScientificJobSummary>(`/scientific-jobs/${encodeURIComponent(publicId)}`); }
  catch (error) {
    if (error instanceof ApiError && [403, 404].includes(error.status)) notFound();
    return <><PageHeader eyebrow="Scientific jobs" title="Scientific job unavailable" description="The request could not be loaded." /><div className="notice" role="alert">The scientific service is unavailable or your session must be renewed. Retry this page; no job state is assumed.</div></>;
  }
  const source = jobSourceHref(job.input_snapshot);
  return <><PageHeader eyebrow="Scientific jobs" title={job.public_id} description="Persisted scientific request, execution state, result and reproducibility provenance." action={source ? <Link className="secondary-button" href={source}>Open current source</Link> : undefined} /><Primer3JobSection title={job.kind === "oligo_primer3_qc" ? "Individual Oligo Primer3 QC" : "Forward/Reverse Assay analysis"} description="Historical result. Re-analysis must be launched from the current source record." jobs={[job]} /></>;
}
