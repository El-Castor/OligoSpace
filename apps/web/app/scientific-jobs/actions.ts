"use server";

import { randomUUID } from "node:crypto";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiWrite, type ScientificJobSummary } from "@/lib/api";
import { actionError, optionalNumber } from "@/lib/form-values";

function parameters(formData: FormData) {
  return {
    mv_conc_mM: optionalNumber(formData, "mv_conc_mM") ?? 50,
    dv_conc_mM: optionalNumber(formData, "dv_conc_mM") ?? 1.5,
    dntp_conc_mM: optionalNumber(formData, "dntp_conc_mM") ?? 0.6,
    dna_conc_nM: optionalNumber(formData, "dna_conc_nM") ?? 50,
    max_loop: optionalNumber(formData, "max_loop") ?? 30,
    max_nn_length: 60,
    tm_method: "santalucia_1998",
    salt_correction_method: "santalucia_1998",
  };
}

export async function runOligoPrimer3(publicId: string, formData: FormData) {
  let job: ScientificJobSummary;
  try {
    job = await apiWrite<ScientificJobSummary>(
      "/scientific-jobs/oligo-primer3-qc",
      "POST",
      { oligo_public_id: publicId, parameters: parameters(formData) },
      { "Idempotency-Key": randomUUID() },
    );
  } catch (error) {
    redirect(`/oligos/${publicId}?scientific_error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath(`/oligos/${publicId}`);
  redirect(`/oligos/${publicId}?scientific_job=${job.public_id}`);
}

export async function runAssayPrimer3(publicId: string, formData: FormData) {
  let job: ScientificJobSummary;
  try {
    job = await apiWrite<ScientificJobSummary>(
      "/scientific-jobs/assay-primer3-pair",
      "POST",
      {
        assay_public_id: publicId,
        forward_oligo_id: formData.get("forward_oligo_id") || null,
        reverse_oligo_id: formData.get("reverse_oligo_id") || null,
        parameters: parameters(formData),
      },
      { "Idempotency-Key": randomUUID() },
    );
  } catch (error) {
    redirect(`/assays/${publicId}?scientific_error=${encodeURIComponent(actionError(error))}`);
  }
  revalidatePath(`/assays/${publicId}`);
  redirect(`/assays/${publicId}?scientific_job=${job.public_id}`);
}
