import { OligoForm } from "@/components/OligoForm";
import { PageHeader } from "@/components/PageHeader";
import { createOligo } from "@/app/oligos/actions";
import { apiGet, type WorkspaceChoices } from "@/lib/api";

export default async function NewOligoPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  const choices = await apiGet<WorkspaceChoices>("/workspace/choices");
  return <><PageHeader eyebrow="Research / oligos" title="Register an oligo" description="OligoSpace normalizes the sequence, rejects exact duplicates, and records calculated screening metrics with their method provenance." /><OligoForm action={createOligo} choices={choices} error={error} /></>;
}
