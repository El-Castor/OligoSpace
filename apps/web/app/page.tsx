import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { apiGetOptional, type DashboardSummary } from "@/lib/api";

export default async function DashboardPage() {
  const summary = await apiGetOptional<DashboardSummary>("/dashboard/summary");
  const stats = [
    ["Shared oligos", summary?.oligos ?? 0, "Biological identities"],
    ["Reusable assays", summary?.assays ?? 0, "Method-specific designs"],
    ["Known targets", summary?.targets ?? 0, "Genes, transcripts, loci"],
    ["Projects", summary?.projects ?? 0, "Collaborative workspaces"],
  ];
  return (
    <>
      <PageHeader
        eyebrow="Workspace overview"
        title="Good science starts with traceable reagents."
        description="Find existing designs before ordering, keep assay context attached, and make every calculated or validated result auditable."
        action={<Link className="primary-button" href="/oligos">Browse oligos</Link>}
      />
      {!summary ? <div className="notice" role="status">The API is not reachable yet. Counts remain at zero; no demonstration data is being substituted.</div> : null}
      <section className="stats" aria-label="Registry summary">
        {stats.map(([label, value, detail]) => (
          <div className="stat" key={label}>
            <div className="stat-label">{label}</div>
            <div className="stat-value">{value}</div>
            <div className="stat-detail">{detail}</div>
          </div>
        ))}
      </section>
      <section className="panel-grid">
        <div className="panel">
          <div className="panel-heading"><h2 className="panel-title">Start with reuse</h2><p className="panel-copy">The shortest path to a trustworthy assay.</p></div>
          <div className="actions">
            <Link className="action" href="/oligos"><span className="action-dot"/><span><strong>Search oligo sequences</strong><span>Check exact identities and calculated QC.</span></span></Link>
            <Link className="action" href="/targets"><span className="action-dot"/><span><strong>Explore biological targets</strong><span>See what the team has already designed.</span></span></Link>
            <Link className="action" href="/assays"><span className="action-dot"/><span><strong>Reuse an assay</strong><span>Keep roles, target, method, and expected product together.</span></span></Link>
          </div>
        </div>
        <div className="panel">
          <div className="panel-heading"><h2 className="panel-title">Scientific status</h2><p className="panel-copy">Truthful gaps that still need evidence.</p></div>
          <div className="empty"><strong>Validation phase not active</strong>Experiment runs and contextual validation arrive in Phase 5.</div>
        </div>
      </section>
    </>
  );
}
