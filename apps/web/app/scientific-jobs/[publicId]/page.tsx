import { notFound } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { Primer3JobSection } from "@/components/Primer3JobSection";
import { apiGetOptional, type ScientificJobSummary } from "@/lib/api";

export default async function ScientificJobDetailPage({ params }: { params: Promise<{ publicId: string }> }) {
  const { publicId } = await params;
  const job = await apiGetOptional<ScientificJobSummary>(`/scientific-jobs/${encodeURIComponent(publicId)}`);
  if (!job) notFound();
  return <><PageHeader eyebrow="Scientific jobs" title={job.public_id} description="Persisted scientific request, execution state, result and reproducibility provenance." /><Primer3JobSection title={job.kind === "oligo_primer3_qc" ? "Individual Oligo Primer3 QC" : "Forward/Reverse Assay analysis"} description="Historical result. Re-analysis must be launched from the current source record." jobs={[job]} /></>;
}
