import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata = {
  title: "Aegis Continuity — Sovereign Resilience-as-Code",
  description:
    "Sovereign Resilience-as-Code and cyber-physical continuity assurance for critical maritime corridors, NATO logistics, Arctic operations, and defense supply chains. Powered by the ContinuityOS Open-Core Engine.",
};

const nav = [
  { href: "/", label: "Home" },
  { href: "/capabilities", label: "Capabilities" },
  { href: "/api", label: "API" },
  { href: "/safety", label: "Safety & ROE" },
  { href: "/quickstart", label: "Quickstart" },
  { href: "/live", label: "Live Deployment" },
  { href: "/cop-dashboard.html", label: "COP Dashboard" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <Link href="/" className="brand">
            Aegis Continuity
          </Link>
          <nav>
            {nav.map((n) => (
              <Link key={n.href} href={n.href}>
                {n.label}
              </Link>
            ))}
          </nav>
          <a
            className="gh"
            href="https://github.com/Hardonian/continuityos"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </header>
        <main>{children}</main>
        <footer className="site-footer">
          <span>
            Aegis Continuity — Powered by the ContinuityOS Open-Core Engine.
          </span>
          <span className="muted">
            Advisory intelligence overlay. Human-in-the-loop. Never autonomous
            kinetic.
          </span>
        </footer>
      </body>
    </html>
  );
}
