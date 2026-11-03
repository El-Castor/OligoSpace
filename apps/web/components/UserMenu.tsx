"use client";

import Link from "next/link";
import { useRef } from "react";

import { LogoutButton } from "@/components/LogoutButton";

import type { CurrentUser } from "@/lib/api";

export function UserMenu({ user }: { user: CurrentUser | null }) {
  const menu = useRef<HTMLDetailsElement>(null);

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
        <Link href="/profile">Profile</Link>
        {user.teams[0] ? <Link href={`/team/${user.teams[0].id}`}>{user.teams[0].name}</Link> : <Link href="/team">Teams</Link>}
        <LogoutButton />
      </div>
    </details>
  );
}
