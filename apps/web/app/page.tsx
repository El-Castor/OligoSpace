import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { apiGet, type CurrentUser, type PersonalizedDashboard } from "@/lib/api";

const resourceHref = (entityType: string, publicId: string) =>
  entityType === "project" ? `/projects/${publicId}` : `/${entityType}s/${publicId}`;

export default async function DashboardPage() {
  const [summary, user] = await Promise.all([
    apiGet<PersonalizedDashboard>("/workspace/dashboard"),
    apiGet<CurrentUser>("/me"),
  ]);
  const stats = [
    ["My oligos", summary.my_oligos, "Created by this identity"],
    ["My assays", summary.my_assays, "Reusable designs I created"],
    ["My projects", summary.my_projects, "Owned or explicit membership"],
    ["Team-shared oligos", summary.team_shared_oligos, "Visible records created by teammates"],
    ["Awaiting validation", summary.awaiting_validation ?? 0, "Visible runs without a current conclusion"],
  ] as const;
  return (
    <>
      <PageHeader eyebrow={`${user.organization_name} · ${user.role.replaceAll("_", " ")}`} title={`Welcome back, ${user.first_name ?? user.display_name}.`} description="Your workspace is derived from your identity, memberships, and server-enforced visibility. No demonstration counts are substituted." action={<Link className="primary-button" href="/projects/new">Create a project</Link>} />
      {user.development_identity ? <div className="development-banner" role="status">Development session · {user.display_name}. Production uses Keycloak OIDC.</div> : null}
      <section className="stats" aria-label="Personal workspace summary">
        {stats.map(([label, value, detail]) => <div className="stat" key={label}><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-detail">{detail}</div></div>)}
      </section>
      <section className="panel-grid">
        <div className="panel"><div className="panel-heading"><h2 className="panel-title">Recent visible resources</h2><p className="panel-copy">Recently created records you can currently access.</p></div>{summary.recent_items.length ? <div className="recent-list">{summary.recent_items.map((item) => <Link href={resourceHref(item.entity_type, item.public_id)} key={`${item.entity_type}-${item.public_id}`}><span className="badge">{item.entity_type}</span><span><strong>{item.name}</strong><small>{item.public_id} · {new Date(item.created_at).toLocaleDateString("en-GB")}</small></span></Link>)}</div> : <div className="empty compact"><strong>No recent resources</strong>Create an oligo, assay, or project to start your workspace history.</div>}</div>
        <div className="panel"><div className="panel-heading"><h2 className="panel-title">My recent activity</h2><p className="panel-copy">Audit events performed by your identity.</p></div>{summary.recent_activity.length ? <div className="activity-list">{summary.recent_activity.slice(0, 8).map((item) => <div key={`${item.entity_id}-${item.occurred_at}`}><span className="action-dot" /><span><strong>{item.action.replaceAll("_", " ")} · {item.entity_type.replaceAll("_", " ")}</strong><small>{new Date(item.occurred_at).toLocaleString("en-GB")}</small></span></div>)}</div> : <div className="empty compact"><strong>No recent activity</strong>Your audited changes will appear here.</div>}</div>
      </section>
      <section className="truthful-gap dashboard-gap"><strong>Later-domain attention</strong><span>Stock alerts remain unavailable until the inventory plan. OligoSpace does not invent those values.</span></section>
    </>
  );
}
