import Link from "next/link";

import { PageHeader } from "@/components/PageHeader";
import { apiGetOptional, type AssaySummary, type OligoSummary, type PageResult, type ProjectSummary, type TargetSummary } from "@/lib/api";

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const query = (await searchParams).q?.trim().slice(0, 200) ?? "";
  if (!query) return <><PageHeader eyebrow="Workspace" title="Search OligoSpace" description="Search public IDs, names, sequences, gene/transcript identifiers, and assay products from the top bar." /><div className="empty-search">Enter a term in global search to find reusable scientific records.</div></>;
  const encoded = encodeURIComponent(query);
  const [oligos, targets, assays, projects] = await Promise.all([apiGetOptional<PageResult<OligoSummary>>(`/registry/oligos?q=${encoded}&limit=20`), apiGetOptional<PageResult<TargetSummary>>(`/registry/targets?q=${encoded}&limit=20`), apiGetOptional<PageResult<AssaySummary>>(`/registry/assays?q=${encoded}&limit=20`), apiGetOptional<ProjectSummary[]>(`/workspace/projects?q=${encoded}`)]);
  const unavailable = !oligos || !targets || !assays || !projects;
  const total = (oligos?.total ?? 0) + (targets?.total ?? 0) + (assays?.total ?? 0) + (projects?.length ?? 0);
  return <><PageHeader eyebrow="Workspace / search" title={`Results for “${query}”`} description={`${total} visible record${total === 1 ? "" : "s"} across the implemented registry and projects.`} />{unavailable ? <div className="notice">Some registry results could not be loaded.</div> : null}<div className="search-results"><SearchSection title="Oligos" href="/oligos" query={query} items={(oligos?.items ?? []).map((item) => ({ id: item.public_id, name: item.name, meta: `${item.sequence_length} nt · ${item.normalized_sequence}`, href: `/oligos/${item.public_id}` }))} /><SearchSection title="Targets" href="/targets" query={query} items={(targets?.items ?? []).map((item) => ({ id: item.public_id, name: item.name, meta: item.gene_identifier ?? item.target_type, href: `/targets/${item.public_id}` }))} /><SearchSection title="Assays" href="/assays" query={query} items={(assays?.items ?? []).map((item) => ({ id: item.public_id, name: item.name, meta: `Version ${item.version}`, href: `/assays/${item.public_id}` }))} /><SearchSection title="Projects" href="/projects" query={query} items={(projects ?? []).map((item) => ({ id: item.public_id, name: item.name, meta: `${item.member_count} members · ${item.visibility}`, href: `/projects/${item.public_id}` }))} /></div></>;
}

function SearchSection({ title, href, query, items }: { title: string; href: string; query: string; items: Array<{ id: string; name: string; meta: string; href: string }> }) {
  return <section className="search-section"><div className="search-section-heading"><h2>{title}</h2><Link className="text-link" href={`${href}?q=${encodeURIComponent(query)}`}>View registry</Link></div>{items.length ? <div className="search-result-list">{items.map((item) => <Link className="search-result" href={item.href} key={item.id}><span className="public-id">{item.id}</span><strong>{item.name}</strong><small>{item.meta}</small></Link>)}</div> : <div className="empty compact">No matching {title.toLowerCase()}.</div>}</section>;
}
