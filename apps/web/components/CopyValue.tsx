"use client";

import { useState } from "react";

export function CopyValue({ value, label }: { value: string; label: string }) {
  const [message, setMessage] = useState("");
  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setMessage("Copied");
    } catch {
      setMessage("Copy unavailable. Select and copy the value manually.");
    }
  }
  return <span className="copy-control"><button className="copy-button" type="button" aria-label={label} onClick={copy}>Copy</button><span className="copy-feedback" role="status">{message}</span></span>;
}
