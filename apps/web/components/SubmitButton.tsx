"use client";

import { useFormStatus } from "react-dom";

export function SubmitButton({ children, className = "primary-button" }: { children: string; className?: string }) {
  const { pending } = useFormStatus();
  return <button className={className} type="submit" disabled={pending} aria-busy={pending} aria-label={children}>{pending ? "Saving…" : children}</button>;
}
