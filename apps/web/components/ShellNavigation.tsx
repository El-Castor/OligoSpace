"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ShellIcon, type ShellIconName } from "@/components/ShellIcon";

const sections: { label: string; items: [string, string, ShellIconName, boolean][] }[] = [
  { label: "Overview", items: [["Overview", "/", "home", false]] },
  { label: "Research", items: [["Oligos", "/oligos", "dna", false], ["Targets", "/targets", "target", false], ["Assays", "/assays", "flask", false], ["Experiments", "/experiments", "chart", false]] },
  { label: "Lab", items: [["Inventory", "/inventory", "box", true], ["Orders", "/orders", "order", true], ["Validation", "/validation", "check", false]] },
  { label: "Workspace", items: [["Projects", "/projects", "folder", false], ["Team", "/team", "users", false]] },
];

function Brand() {
  return <Link className="brand" href="/" aria-label="OligoSpace overview"><span className="brand-mark"><ShellIcon name="dna" size={38} /></span><span className="brand-copy"><span className="brand-name">OligoSpace</span><span className="brand-subtitle">Scientific registry</span></span></Link>;
}

export function ShellNavigation({ isAdmin }: { isAdmin: boolean }) {
  const pathname = usePathname();
  const drawer = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false);
  useEffect(() => { drawer.current?.close(); }, [pathname]);
  useEffect(() => {
    const desktop = matchMedia("(min-width: 768px)");
    const close = () => { if (desktop.matches) drawer.current?.close(); };
    desktop.addEventListener("change", close);
    return () => desktop.removeEventListener("change", close);
  }, []);
  function navigation() {
    const groups = isAdmin ? [...sections, { label: "System", items: [["Admin", "/admin", "settings", false] as [string, string, ShellIconName, boolean]] }] : sections;
    return <nav aria-label="Primary navigation">{groups.map((section) => <div className="nav-group" key={section.label}><div className="nav-label">{section.label}</div>{section.items.map(([label, href, icon, planned]) => {
      const active = href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
      return <Link className="nav-link" href={href} key={href} aria-current={active ? "page" : undefined} onClick={() => drawer.current?.close()}><span className="nav-icon"><ShellIcon name={icon} /></span><span>{label}</span>{planned ? <span className="planned">Next</span> : null}</Link>;
    })}</div>)}</nav>;
  }
  return <>
    <aside className="sidebar"><Brand />{navigation()}<p className="sidebar-footnote">Scientific workspace</p></aside>
    <button type="button" className="navigation-toggle" aria-label="Open navigation" aria-haspopup="dialog" aria-expanded={open} aria-controls="mobile-navigation" onClick={() => { drawer.current?.showModal(); setOpen(true); }}><ShellIcon name="menu" /></button>
    <dialog id="mobile-navigation" className="mobile-navigation" aria-label="Navigation" ref={drawer} onClose={() => setOpen(false)} onKeyDown={(event) => {
      if (event.key !== "Tab") return;
      const controls = event.currentTarget.querySelectorAll<HTMLElement>("a[href], button:not([disabled])");
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first?.focus();
      }
    }} onClick={(event) => {
      if (event.target === event.currentTarget) {
        const bounds = event.currentTarget.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) drawer.current?.close();
      }
    }}>
      <button type="button" className="navigation-close" aria-label="Close navigation" onClick={() => drawer.current?.close()}><ShellIcon name="close" /></button>
      <Brand />{navigation()}
    </dialog>
  </>;
}

export function ShellLocation() {
  const pathname = usePathname();
  const entry = sections.flatMap((section) => section.items).find(([, href]) => href !== "/" && (pathname === href || pathname.startsWith(`${href}/`)));
  const label = entry?.[0] ?? (pathname.startsWith("/admin") ? "Administration" : pathname.startsWith("/profile") ? "Profile" : pathname.startsWith("/search") ? "Search" : "Overview");
  return <nav className="shell-location" aria-label="Section navigation"><Link href={entry?.[1] ?? (label === "Administration" ? "/admin" : label === "Profile" ? "/profile" : label === "Search" ? "/search" : "/")}>{label}</Link>{entry && pathname !== entry[1] ? <><span aria-hidden="true">/</span><span>{pathname.endsWith("/new") ? "New record" : "Record"}</span></> : null}</nav>;
}
