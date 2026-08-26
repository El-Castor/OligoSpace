import type { Metadata } from "next";

import { AppShell } from "@/components/AppShell";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "OligoSpace", template: "%s · OligoSpace" },
  description: "Collaborative oligonucleotide and assay registry",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><AppShell>{children}</AppShell></body>
    </html>
  );
}
