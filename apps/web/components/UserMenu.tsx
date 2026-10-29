"use client";

import Link from "next/link";
import { signOut } from "next-auth/react";
import { useState } from "react";

import type { CurrentUser } from "@/lib/api";

export function UserMenu({ user }: { user: CurrentUser | null }) {
  const [signingOut, setSigningOut] = useState(false);

  async function logout() {
    setSigningOut(true);
    const response = await fetch("/api/auth/logout-url", { cache: "no-store" });
    const payload = (await response.json()) as { url: string };
    await signOut({ redirect: false });
    window.location.assign(payload.url);
  }

  if (!user) return <div className="avatar" aria-label="No active user">?</div>;
  return (
    <details className="user-menu">
      <summary className="avatar" aria-label="Current user">{user.initials}</summary>
      <div className="user-popover">
        <div className="user-identity">
          <strong>{user.display_name}</strong>
          <span>{user.email}</span>
          <small>{user.development_identity ? "Development identity" : user.organization_name}</small>
        </div>
        <Link href="/profile">Profile</Link>
        {user.teams[0] ? <Link href={`/team/${user.teams[0].id}`}>{user.teams[0].name}</Link> : <Link href="/team">Teams</Link>}
        <button type="button" onClick={logout} disabled={signingOut}>
          {signingOut ? "Signing out…" : "Logout"}
        </button>
      </div>
    </details>
  );
}
