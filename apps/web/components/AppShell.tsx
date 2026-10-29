import Link from "next/link";
import type { ReactNode } from "react";

import { UserMenu } from "@/components/UserMenu";
import { apiGetOptional, type CurrentUser } from "@/lib/api";

const sections = [
  { label: "Overview", items: [["Overview", "/", "01", false]] },
  {
    label: "Research",
    items: [
      ["Oligos", "/oligos", "AT", false],
      ["Targets", "/targets", "TG", false],
      ["Assays", "/assays", "AS", false],
      ["Experiments", "/experiments", "EX", false],
    ],
  },
  {
    label: "Lab",
    items: [
      ["Inventory", "/inventory", "IN", true],
      ["Orders", "/orders", "OR", true],
      ["Validation", "/validation", "VA", false],
    ],
  },
  {
    label: "Workspace",
    items: [
      ["Projects", "/projects", "PR", false],
      ["Team", "/team", "TM", false],
    ],
  },
] as const;

export async function AppShell({ children }: { children: ReactNode }) {
  const user = await apiGetOptional<CurrentUser>("/me");
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/" aria-label="OligoSpace overview">
          <span className="brand-mark">OS</span>
          <span className="brand-copy">
            <span className="brand-name">OligoSpace</span>
            <span className="brand-subtitle">Scientific registry</span>
          </span>
        </Link>
        <nav aria-label="Primary navigation">
          {sections.map((section) => (
            <div className="nav-group" key={section.label}>
              <div className="nav-label">{section.label}</div>
              {section.items.map(([label, href, icon, planned]) => (
                <Link className="nav-link" href={href} key={href}>
                  <span className="nav-icon" aria-hidden="true">{icon}</span>
                  <span>{label}</span>
                  {planned ? <span className="planned">Next</span> : null}
                </Link>
              ))}
            </div>
          ))}
          {user?.role === "admin" ? (
            <div className="nav-group">
              <div className="nav-label">System</div>
              <Link className="nav-link" href="/admin">
                <span className="nav-icon" aria-hidden="true">AD</span>
                <span>Admin</span>
              </Link>
            </div>
          ) : null}
        </nav>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <form className="search" action="/search" role="search">
            <span aria-hidden="true">⌕</span>
            <input name="q" aria-label="Global search" placeholder="Search IDs, sequences, genes, assays…" />
          </form>
          <UserMenu user={user} />
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
