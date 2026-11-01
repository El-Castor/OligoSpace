import type { ReactNode } from "react";

import { ShellNavigation, ShellLocation } from "@/components/ShellNavigation";
import { ShellIcon } from "@/components/ShellIcon";
import { UserMenu } from "@/components/UserMenu";
import { FormDraftProvider } from "@/components/FormDraftProvider";
import { apiGetOptional, type CurrentUser } from "@/lib/api";

export async function AppShell({ children }: { children: ReactNode }) {
  const user = await apiGetOptional<CurrentUser>("/me");
  return (
    <div className="app-shell">
      <a className="skip-content" href="#main-content">Skip to content</a>
      <ShellNavigation isAdmin={user?.role === "admin"} />
      <div className="workspace">
        <header className="topbar">
          <ShellLocation />
          <form className="search" action="/search" role="search">
            <ShellIcon name="search" size={19} />
            <input name="q" aria-label="Global search" placeholder="Search IDs, sequences, genes, assays…" />
          </form>
          <UserMenu user={user} />
        </header>
        <main className="content" id="main-content" tabIndex={-1}><FormDraftProvider key={user?.id ?? "anonymous"}>{children}</FormDraftProvider></main>
      </div>
    </div>
  );
}
