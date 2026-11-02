"use client";

import Link from "next/link";
import { signOut } from "next-auth/react";
import { useRef, useState } from "react";

import type { CurrentUser } from "@/lib/api";

export function UserMenu({ user }: { user: CurrentUser | null }) {
  const [signingOut, setSigningOut] = useState(false);
  const [logoutFailed, setLogoutFailed] = useState(false);
  const menu = useRef<HTMLDetailsElement>(null);

  async function logout() {
    setSigningOut(true);
    try {
      // NextAuth POST signout validates CSRF; the server event closes Keycloak.
      await signOut({ callbackUrl: "/login" });
    } catch {
      setSigningOut(false);
      setLogoutFailed(true);
    }
  }

  if (!user) return <div className="avatar" aria-label="No active user">?</div>;
  return (
    <details className="user-menu" ref={menu} onKeyDown={(event) => {
      if (event.key === "Escape") {
        menu.current?.removeAttribute("open");
        menu.current?.querySelector("summary")?.focus();
      }
    }} onBlur={(event) => {
      if (!event.currentTarget.contains(event.relatedTarget)) menu.current?.removeAttribute("open");
    }}>
      <summary className="avatar" aria-label="Current user">{user.initials}</summary>
      <div className="user-popover">
        <div className="user-identity">
          <strong>{user.display_name}</strong>
          <span>{user.email}</span>
          <small>{user.development_identity ? "Development identity" : user.organization_name}</small>
        </div>
        {logoutFailed ? <p role="alert">Logout could not be completed. Please retry.</p> : null}
        <Link href="/profile">Profile</Link>
        {user.teams[0] ? <Link href={`/team/${user.teams[0].id}`}>{user.teams[0].name}</Link> : <Link href="/team">Teams</Link>}
        <button type="button" onClick={logout} disabled={signingOut}>
          {signingOut ? "Signing out…" : "Logout"}
        </button>
      </div>
    </details>
  );
}
