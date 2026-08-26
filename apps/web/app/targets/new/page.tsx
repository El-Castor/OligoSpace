import { createTarget } from "@/app/targets/actions";
import { PageHeader } from "@/components/PageHeader";
import { TargetForm } from "@/components/TargetForm";
import { apiGetOptional, type Organism } from "@/lib/api";

export default async function NewTargetPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  const organisms = await apiGetOptional<Organism[]>("/registry/organisms");
  return <><PageHeader eyebrow="Research / targets" title="Register a target" description="Record only known identifiers and reference sequence. Mapping and coordinates are never inferred from a label." />{!organisms ? <div className="notice">The organism catalog is unavailable; the target can still be recorded without one.</div> : null}<TargetForm action={createTarget} organisms={organisms ?? []} error={error} /></>;
}
