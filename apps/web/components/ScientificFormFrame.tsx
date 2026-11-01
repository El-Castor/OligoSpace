"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { useFormStatus } from "react-dom";
import { useFormDraft } from "@/components/FormDraftProvider";

type Draft = Array<{ name: string; index: number; value: string; checked: boolean }>;
type Control = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
function controls(form: HTMLFormElement): Control[] {
  return Array.from(form.elements).filter((element): element is Control => element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement);
}
function remembered(element: Control) {
  return element.name && !element.disabled && !(element instanceof HTMLInputElement && ["hidden", "file", "password", "submit", "button"].includes(element.type)) && !("readOnly" in element && element.readOnly);
}
function Feedback({ error, onFailure }: { error?: string; onFailure: () => void }) {
  const { pending } = useFormStatus();
  const summary = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!error || pending) return;
    onFailure();
    summary.current?.focus();
  }, [error, pending, onFailure]);
  return <>{error ? <div className="notice form-error" role="alert" tabIndex={-1} ref={summary}><strong>Save not confirmed</strong><span>{error}</span></div> : null}{pending ? <p className="form-pending" role="status">Saving. Waiting for the server to confirm.</p> : null}</>;
}

export function ScientificFormFrame({ action, error, children, className = "record-form", legend = true, preserveDraft = true }: { action: (data: FormData) => void | Promise<void>; error?: string; children: ReactNode; className?: string; legend?: boolean; preserveDraft?: boolean }) {
  const form = useRef<HTMLFormElement>(null);
  const draft = useRef<Draft | null>(null);
  const [dirty, setDirty] = useState(false);
  const sharedDraft = useFormDraft();
  const restoreDraft = useCallback(() => {
    const shared = sharedDraft?.take();
    const submitted = draft.current ?? shared;
    if (!submitted || !form.current) return;
    const fields = controls(form.current);
    for (const entry of submitted) {
      const element = fields.filter((field) => field.name === entry.name)[entry.index];
      if (!element || !remembered(element)) continue;
      if (element instanceof HTMLSelectElement && !Array.from(element.options).some((option) => option.value === entry.value && !option.disabled)) continue;
      element.value = entry.value;
      if (element instanceof HTMLInputElement && ["checkbox", "radio"].includes(element.type)) element.checked = entry.checked;
    }
    draft.current = null;
  }, [sharedDraft]);
  return <form className={className} action={action} ref={form} onChange={() => setDirty(true)} onSubmit={() => {
    if (!preserveDraft) { draft.current = null; sharedDraft?.remember([]); return; }
    const fields = controls(form.current!);
    draft.current = fields.filter(remembered).map((element) => ({ name: element.name, index: fields.filter((field) => field.name === element.name).indexOf(element), value: element.value, checked: element instanceof HTMLInputElement && element.checked }));
    sharedDraft?.remember(draft.current);
  }}>
    {legend ? <p className="form-conventions">Fields marked * are required. Other fields are optional unless stated otherwise.</p> : null}
    <Feedback error={error} onFailure={restoreDraft} />
    <p className="form-dirty" aria-live="polite">{dirty ? "Unsaved changes" : "Ready to edit"}</p>
    {children}
  </form>;
}
