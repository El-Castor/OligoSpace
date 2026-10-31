const paths = {
  dna: "M7 3c0 8 10 10 10 18M17 3C17 11 7 13 7 21M8 5h8M9 9h6M9 15h6M8 19h8",
  home: "m3 11 9-8 9 8M5 10v11h5v-7h4v7h5V10",
  flask: "M9 3h6M10 3v7L4 20c-.4.7 0 1 1 1h14c1 0 1.4-.3 1-1l-6-10V3M7 16h10",
  folder: "M3 6h7l2 3h9v12H3ZM3 6V3h7l2 3h9v3",
  chart: "M4 21V11h3v10M11 21V3h3v18M18 21v-7h3v7",
  job: "M5 3h14v18H5ZM9 7h6M9 11h6M9 15h4",
  search: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14m5 12 6 6",
  plus: "M12 5v14M5 12h14",
  book: "M3 4h6l3 2 3-2h6v16h-6l-3 2-3-2H3ZM12 6v16",
  check: "m5 12 4 4L19 6",
  menu: "M4 6h16M4 12h16M4 18h16",
  warning: "m12 3 10 18H2ZM12 9v5M12 17v.1",
  copy: "M8 8h13v13H8ZM16 5V2H2v14h3",
  arrow: "m9 5 7 7-7 7",
} as const;

export function Icon({ name, size = 22 }: { name: keyof typeof paths; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>;
}
