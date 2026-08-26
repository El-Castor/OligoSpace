import Link from "next/link";
import type { ReactNode } from "react";

const sections = [
  { label: "Overview", items: [["Overview", "/", "01", false]] },
  {
    label: "Research",
    items: [
      ["Oligos", "/oligos", "AT", false],
      ["Targets", "/targets", "TG", false],
      ["Assays", "/assays", "AS", false],
      ["Experiments", "/experiments", "EX", true],
    ],
  },
  {
    label: "Lab",
    items: [
      ["Inventory", "/inventory", "IN", true],
      ["Orders", "/orders", "OR", true],
      ["Validation", "/validation", "VA", true],
    ],
  },
  {
    label: "Workspace",
    items: [
      ["Projects", "/projects", "PR", true],
      ["Team", "/team", "TM", true],
    ],
  },
  { label: "System", items: [["Admin", "/admin", "AD", true]] },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
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
        </nav>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <label className="search">
            <span aria-hidden="true">⌕</span>
            <input aria-label="Global search" placeholder="Search IDs, sequences, genes, assays…" disabled />
          </label>
          <div className="avatar" aria-label="Current user">LA</div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
