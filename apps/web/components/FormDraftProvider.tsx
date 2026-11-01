"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, type ReactNode } from "react";
import { usePathname } from "next/navigation";

export type FormDraft = Array<{ name: string; index: number; value: string; checked: boolean }>;
type DraftAccess = { remember: (value: FormDraft) => void; take: () => FormDraft | null };
const Context = createContext<DraftAccess | null>(null);

// One submitted draft, only in memory. A route or identity change drops it.
export function FormDraftProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const saved = useRef<{ pathname: string; value: FormDraft } | null>(null);
  const remember = useCallback((value: FormDraft) => { saved.current = { pathname, value }; }, [pathname]);
  const take = useCallback(() => {
    const value = saved.current?.pathname === pathname ? saved.current.value : null;
    saved.current = null;
    return value;
  }, [pathname]);
  useEffect(() => { if (saved.current?.pathname !== pathname) saved.current = null; }, [pathname]);
  const access = useMemo(() => ({ remember, take }), [remember, take]);
  return <Context.Provider value={access}>{children}</Context.Provider>;
}

export function useFormDraft() { return useContext(Context); }
