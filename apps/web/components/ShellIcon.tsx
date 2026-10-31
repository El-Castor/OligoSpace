const paths = {
  dna: "M7 3c0 8 10 10 10 18M17 3C17 11 7 13 7 21M8 5h8M9 9h6M9 15h6M8 19h8",
  home: "m3 11 9-8 9 8M5 10v11h5v-7h4v7h5V10",
  target: "M21 12a9 9 0 1 1-9-9M16 12a4 4 0 1 1-4-4M12 12l9-9M16 3h5v5",
  flask: "M9 3h6M10 3v7L4 20c-.4.7 0 1 1 1h14c1 0 1.4-.3 1-1l-6-10V3M7 16h10",
  folder: "M3 6h7l2 3h9v12H3ZM3 6V3h7l2 3h9v3",
  chart: "M4 21V11h3v10M11 21V3h3v18M18 21v-7h3v7",
  check: "m5 12 4 4L19 6",
  menu: "M4 6h16M4 12h16M4 18h16",
  close: "m6 6 12 12M6 18 18 6",
  search: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14m5 12 6 6",
  users: "M16 21v-3c0-3-3-4-6-4s-6 1-6 4v3M14 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0M17 4a4 4 0 0 1 0 8M20 21v-3c0-2-1-3-3-4",
  box: "m3 7 9-4 9 4v10l-9 4-9-4ZM3 7l9 4 9-4M12 11v10",
  order: "M5 3h14v18H5ZM9 7h6M9 11h6M9 15h4",
  settings: "M12 3v3M12 18v3M3 12h3M18 12h3M5 5l3 3M16 16l3 3M5 19l3-3M16 8l3-3M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
} as const;

export type ShellIconName = keyof typeof paths;
export function ShellIcon({ name, size = 22 }: { name: ShellIconName; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>;
}
