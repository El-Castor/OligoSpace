"use client";

import { signOut } from "next-auth/react";
import { useState } from "react";

export function LogoutButton({ className }: { className?: string }) {
  const [signingOut, setSigningOut] = useState(false);
  const [failed, setFailed] = useState(false);
  async function logout() {
    setSigningOut(true);
    setFailed(false);
    try {
      const response = await fetch("/api/auth/provider-logout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
        cache: "no-store",
      });
      if (!response.ok) throw new Error("provider_logout_not_confirmed");
      await signOut({ callbackUrl: "/login" });
    } catch {
      setSigningOut(false);
      setFailed(true);
    }
  }
  return <>
    {failed ? <p role="alert">Logout could not be completed. Please retry.</p> : null}
    <button type="button" className={className} onClick={logout} disabled={signingOut}>
      {signingOut ? "Signing out…" : "Logout"}
    </button>
  </>;
}
