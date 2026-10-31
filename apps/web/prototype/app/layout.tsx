import type { Metadata } from "next";
import "./tokens.css";
import "./prototype.css";

export const metadata: Metadata = {
  title: "Scientific Soft UI · OligoSpace prototype",
  robots: { index: false, follow: false },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="fr"><body>{children}</body></html>;
}
