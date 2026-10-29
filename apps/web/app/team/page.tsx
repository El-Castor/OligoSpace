import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { apiGet, type TeamSummary } from "@/lib/api";

export default async function TeamsPage() {
  const teams = await apiGet<TeamSummary[]>("/workspace/teams");
  return (
    <>
      <PageHeader eyebrow="Workspace" title="My teams" description="Institute teams and membership roles that currently grant you access." />
      {teams.length ? <section className="card-grid" aria-label="Teams">{teams.map((team) => <Link className="workspace-card" href={`/team/${team.id}`} key={team.id}><span className="card-kicker">{team.current_user_role?.replaceAll("_", " ")}</span><h2>{team.name}</h2><p>{team.description ?? "No team description yet."}</p><span>{team.member_count} members · {team.active ? "Active" : "Inactive"}</span></Link>)}</section> : <div className="empty-search"><strong>No team membership</strong><p>An administrator or team manager can add your projected user to a team.</p></div>}
    </>
  );
}
