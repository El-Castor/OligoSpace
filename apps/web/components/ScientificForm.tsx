import type { ComponentProps } from "react";
import { apiGet, type CurrentUser } from "@/lib/api";
import { ScientificFormFrame } from "@/components/ScientificFormFrame";

export async function ScientificForm(props: ComponentProps<typeof ScientificFormFrame>) {
  const current = await apiGet<CurrentUser>("/me");
  if (current.role === "viewer") return <div className="notice" role="alert"><strong>Read-only access</strong><p>Your current role cannot submit scientific resource changes. Records remain available through the navigation.</p></div>;
  return <ScientificFormFrame {...props} />;
}
