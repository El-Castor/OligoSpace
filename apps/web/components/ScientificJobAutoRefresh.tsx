"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import { startJobPolling } from "@/lib/scientific-polling";

export function ScientificJobAutoRefresh({ active }: { active: boolean }) {
  const router = useRouter();
  const [exhausted, setExhausted] = useState(false);
  const [pending, startTransition] = useTransition();
  useEffect(() => {
    if (!active) return;
    const reset = window.setTimeout(() => setExhausted(false), 0);
    const cancel = startJobPolling(() => router.refresh(), () => setExhausted(true), (tick, delay) => {
      const interval = window.setInterval(tick, delay);
      return () => window.clearInterval(interval);
    });
    return () => { window.clearTimeout(reset); cancel(); };
  }, [active, router]);
  if (!active) return null;
  return <div className="job-refresh"><p role="status">{exhausted ? "Automatic refresh paused after one minute. This is the last observed server state." : "Reading the server state automatically. No completion percentage is available."}</p><button className="secondary-button" type="button" disabled={pending} onClick={() => startTransition(() => router.refresh())}>Refresh job status</button></div>;
}
