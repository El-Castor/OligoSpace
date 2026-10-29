"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export function ScientificJobAutoRefresh({ active }: { active: boolean }) {
  const router = useRouter();
  useEffect(() => {
    if (!active) return;
    let refreshes = 0;
    const interval = window.setInterval(() => {
      refreshes += 1;
      router.refresh();
      if (refreshes >= 40) window.clearInterval(interval);
    }, 1500);
    return () => window.clearInterval(interval);
  }, [active, router]);
  return null;
}
