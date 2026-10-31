"use client";

import { useRef, useState, type FormEvent, type ReactNode } from "react";
import { Icon } from "./Icon";
import { demoOligos, type DemoOligo, type DemoStatus } from "./data";

function Panel({ title, icon, children, id, className = "" }: {
  title: string; icon: Parameters<typeof Icon>[0]["name"]; children: ReactNode; id?: string; className?: string;
}) {
  return <section className={`su-panel ${className}`} id={id} aria-label={title}>
    <h2><Icon name={icon} />{title}</h2>{children}
  </section>;
}

function StatusBadge({ status }: { status: DemoStatus }) {
  return <span className="su-badge" data-status={status}>
    {status === "À revoir" ? <Icon name="warning" size={14} /> : <span aria-hidden="true">{status === "Actif" ? "●" : "▣"}</span>}{status}
  </span>;
}

function Sidebar() {
  const [open, setOpen] = useState(false);
  return <aside className="su-sidebar">
    <a className="su-brand" href="#overview"><Icon name="dna" size={40} /><span><strong>OligoSpace</strong><small>Scientific registry</small></span></a>
    <button className="su-mobile-menu" aria-expanded={open} aria-controls="prototype-navigation" onClick={() => setOpen(!open)}><Icon name="menu" />Navigation</button>
    <nav id="prototype-navigation" aria-label="Navigation du prototype" data-open={open}>
      {([
        ["home", "Vue d’ensemble", "overview"], ["dna", "Oligos", "oligos"],
        ["flask", "Assays", "analyses"], ["chart", "Expériences", "analyses"], ["folder", "Projets", "new-oligo"],
      ] as const).map(([icon, label, anchor]) => <a href={`#${anchor}`} key={label} className={label === "Oligos" ? "su-nav-active" : ""} onClick={() => setOpen(false)}><Icon name={icon} />{label}</a>)}
    </nav>
    <div className="su-profile"><span className="su-avatar" aria-hidden="true">AD</span><span><strong>Atelier de design</strong><small>Profil fictif · sans connexion</small></span></div>
  </aside>;
}

function Metrics({ added }: { added: number }) {
  return <div className="su-metrics" aria-label="Statistiques fictives">
    {([
      ["dna", 248 + added, "Oligonucléotides"], ["flask", 24, "Assays"], ["job", 6, "Jobs scientifiques"],
    ] as const).map(([icon, value, label]) => <div className="su-metric" key={label}><span className="su-metric-icon"><Icon name={icon} size={28} /></span><div><strong>{value}</strong><span>{label}</span><small>Exemple fictif</small></div></div>)}
  </div>;
}

function OligoForm({ onAdd }: { onAdd: (name: string, sequence: string) => void }) {
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const formRef = useRef<HTMLFormElement>(null);
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const name = String(data.get("name") ?? "").trim();
    const sequence = String(data.get("sequence") ?? "").replaceAll(/\s/g, "").toUpperCase();
    if (!name || !/^[ACGT]+$/.test(sequence)) {
      setError("Pour cette simulation, saisir un nom et une séquence composée de A, C, G et T.");
      setNotice("");
      return;
    }
    onAdd(name, sequence);
    setError("");
    setNotice("Ajout fictif en mémoire uniquement. Il sera effacé au rechargement.");
    formRef.current?.reset();
  }
  return <Panel title="Nouvel oligo" icon="plus" id="new-oligo">
    <form className="su-form" onSubmit={submit} ref={formRef}>
      <label><span>Nom de l’oligo <span aria-hidden="true">*</span></span><input name="name" required maxLength={120} placeholder="Ex. Bd21 · floraison / F" /></label>
      <label><span>Séquence 5′ → 3′ <span aria-hidden="true">*</span></span><textarea name="sequence" required maxLength={120} rows={3} placeholder="Ex. ATGAGTGATATCGCCGTT" aria-describedby="sequence-help" aria-invalid={error ? true : undefined} /></label>
      <p className="su-help" id="sequence-help">A, T, C, G · séquence synthétique de démonstration. Aucune validation scientifique.</p>
      <label>Projet<select name="project" defaultValue=""><option value="" disabled>Sélectionner un projet fictif</option><option value="demo">Brachypodium · développement</option><option value="controls">Témoins végétaux</option></select></label>
      {error ? <p className="su-error" role="alert">{error}</p> : null}
      <button type="submit" className="su-button su-primary"><Icon name="plus" size={18} />Simuler la création</button>
      <p className="su-help su-inline"><span aria-hidden="true">ⓘ</span>Démonstration locale uniquement. Aucune sauvegarde.</p>
      <p className="su-form-notice" role="status">{notice}</p>
    </form>
  </Panel>;
}

function OligoLibrary({ rows }: { rows: readonly DemoOligo[] }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("Tous les statuts");
  const [density, setDensity] = useState("comfortable");
  const [copied, setCopied] = useState("");
  const filtered = rows.filter((row) => (status === "Tous les statuts" || row.status === status) &&
    `${row.id} ${row.name} ${row.organism ?? ""} ${row.sequence}`.toLowerCase().includes(query.trim().toLowerCase()));
  async function copy(row: DemoOligo) {
    try {
      await navigator.clipboard.writeText(row.sequence);
      setCopied(`Séquence ${row.id} copiée.`);
    } catch {
      setCopied("Copie indisponible. Sélectionnez la séquence pour la copier manuellement.");
    }
  }
  return <Panel title="Bibliothèque d’oligos" icon="dna" id="oligos" className="su-library">
    <p className="su-library-context">Exemples de biologie végétale · <i>Brachypodium distachyon</i> et témoins</p>
    <div className="su-toolbar">
      <label className="su-query"><span className="su-sr-only">Rechercher un oligo fictif</span><Icon name="search" size={18} /><input type="search" value={query} placeholder="Nom, identifiant ou séquence…" onChange={(event) => setQuery(event.target.value)} /></label>
      <label>Statut<select aria-label="Statut" value={status} onChange={(event) => setStatus(event.target.value)}><option>Tous les statuts</option><option>Actif</option><option>À revoir</option><option>Archivé</option></select></label>
      <fieldset className="su-density"><legend>Affichage</legend><div>{[["comfortable", "Confortable"], ["compact", "Compact"]].map(([value, label]) => <button key={value} type="button" aria-pressed={density === value} onClick={() => setDensity(value)}>{label}</button>)}</div></fieldset>
    </div>
    <div className="su-table-scroll" role="region" aria-label="Tableau des oligos fictifs, défilement horizontal" tabIndex={0}>
      <table className="su-table" data-density={density}>
        <caption>{filtered.length} exemple{filtered.length > 1 ? "s" : ""} visible{filtered.length > 1 ? "s" : ""} · données entièrement fictives</caption>
        <thead><tr><th scope="col">Identifiant</th><th scope="col">Nom</th><th scope="col">Séquence 5′ → 3′</th><th scope="col">Statut</th></tr></thead>
        <tbody>{filtered.map((row) => <tr key={row.id}><td className="su-id">{row.id}</td><td><span className="su-oligo-name">{row.name}</span>{row.organism ? <i className="su-organism">{row.organism}</i> : <span className="su-organism">Simulation locale</span>}</td><td><span className="su-sequence">{row.sequence}</span><button className="su-copy" type="button" aria-label={`Copier la séquence ${row.id}`} onClick={() => copy(row)}><Icon name="copy" size={15} /></button></td><td><StatusBadge status={row.status} /></td></tr>)}</tbody>
      </table>
    </div>
    {filtered.length === 0 ? <div className="su-empty"><Icon name="search" size={28} /><strong>Aucun oligo ne correspond</strong><p>Essayez un autre terme ou réinitialisez les filtres.</p><button className="su-button" onClick={() => { setQuery(""); setStatus("Tous les statuts"); }}>Réinitialiser les filtres</button></div> : null}
    <p className="su-copy-notice" role="status">{copied}</p>
  </Panel>;
}

function ScientificJobs() {
  const [paused, setPaused] = useState(false);
  return <Panel title="Analyses Primer3" icon="flask" id="analyses">
    <p className="su-description">Simulation visuelle · aucun calcul scientifique</p>
    {[{ id: "DEMO-OLG-001", value: 75, label: "Préparation des paramètres" }, { id: "DEMO-OLG-003", value: 30, label: "En attente d’un créneau" }].map((job) => <div className="su-job" key={job.id}>
      <div><strong>{job.id}</strong><small>{paused ? "Simulation en pause" : job.label}</small></div>
      <div className="su-progress"><progress aria-label={`Progression simulée ${job.id}`} value={job.value} max={100} /><span>{job.value} %</span></div>
      <span className="su-help">Fictif · sans résultat</span>
    </div>)}
    <button className="su-button su-quiet" type="button" aria-pressed={paused} onClick={() => setPaused(!paused)}>{paused ? "Reprendre la simulation" : "Mettre en pause la simulation"}</button>
  </Panel>;
}

function ComponentStates() {
  const [state, setState] = useState("Normal");
  return <Panel title="États des composants" icon="job" id="components">
    <div className="su-state-buttons" role="group" aria-label="État à prévisualiser">
      {["Normal", "Chargement", "Erreur", "Vide"].map((value) => <button type="button" key={value} aria-pressed={state === value} onClick={() => setState(value)}>{value}</button>)}
    </div>
    <div className="su-state-content">
      {state === "Normal" ? <><label>Champ de saisie<input placeholder="Valeur d’exemple" /></label><div className="su-component-samples"><StatusBadge status="Actif" /><button className="su-button" onClick={() => setState("Chargement")}>Prévisualiser</button><button className="su-button" disabled>Indisponible</button></div><p className="su-help">Action désactivée dans cet exemple.</p></> : null}
      {state === "Chargement" ? <div role="status" aria-live="polite"><div className="su-skeleton" aria-hidden="true" /><strong>Chargement de démonstration…</strong><p>Aucune requête n’est envoyée.</p></div> : null}
      {state === "Erreur" ? <div role="alert" className="su-error"><Icon name="warning" /><strong>Impossible de charger cet exemple.</strong><p>État simulé : vos données ne sont pas concernées.</p><button className="su-button" onClick={() => setState("Normal")}>Réessayer la démonstration</button></div> : null}
      {state === "Vide" ? <div className="su-empty"><Icon name="folder" size={28} /><strong>Aucun résultat dans cet exemple</strong><p>Un état vide explique la prochaine action.</p><button className="su-button" onClick={() => setState("Normal")}>Revenir aux composants</button></div> : null}
    </div>
  </Panel>;
}

export function SoftUIPrototype() {
  const [added, setAdded] = useState<DemoOligo[]>([]);
  return <div className="soft-ui" data-soft-ui>
    <a className="su-skip" href="#prototype-main">Aller au contenu</a>
    <Sidebar />
    <main className="su-main" id="prototype-main" tabIndex={-1}>
      <p className="su-prototype-notice"><span aria-hidden="true">ⓘ</span>Prototype · Données fictives · Aucune sauvegarde</p>
      <header className="su-heading" id="overview"><div><h1>Un espace clair pour la science.</h1><p>Concevoir, retrouver et réutiliser les oligos du laboratoire.</p></div><a className="su-button" href="#components"><Icon name="book" size={20} />Guide des composants</a></header>
      <Metrics added={added.length} />
      <div className="su-main-grid"><OligoLibrary rows={[...demoOligos, ...added]} /><OligoForm onAdd={(name, sequence) => setAdded((previous) => [...previous, { id: `DEMO-LOCAL-${String(previous.length + 1).padStart(3, "0")}`, name, sequence, status: "À revoir" }])} /></div>
      <div className="su-bottom-grid"><ScientificJobs /><ComponentStates /></div>
      <footer className="su-footer">Atelier Scientific Soft UI · Les séquences, collections et jobs sont fictifs. Aucun résultat biologique ne peut être déduit de cette démonstration.</footer>
    </main>
  </div>;
}
