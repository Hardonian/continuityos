import type { ReactNode } from "react";
import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "./globals.css";
import SiteNav from "./components/SiteNav";
import StructuredData from "./components/StructuredData";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://continuityos.com"),
  title: {
    default: "ContinuityOS / Aegis Continuity — Sovereign Resilience-as-Code",
    template: "%s — ContinuityOS",
  },
  description:
    "Sovereign Resilience-as-Code and cyber-physical continuity assurance for critical maritime corridors, NATO logistics, Arctic operations, and defense supply chains. Powered by the ContinuityOS Engine.",
  applicationName: "ContinuityOS",
  keywords: [
    "continuity assurance",
    "resilience-as-code",
    "maritime corridor",
    "NATO logistics",
    "Arctic operations",
    "defense supply chain",
    "cyber-physical",
    "sovereign AI",
    "decision evidence",
    "ITSG-33",
    "Protected B",
  ],
  openGraph: {
    type: "website",
    siteName: "ContinuityOS",
    title: "ContinuityOS / Aegis Continuity — Sovereign Resilience-as-Code",
    description:
      "Sovereign Resilience-as-Code and cyber-physical continuity assurance for critical maritime corridors, NATO logistics, and defense supply chains.",
    url: "https://continuityos.com",
  },
  twitter: {
    card: "summary_large_image",
    title: "ContinuityOS / Aegis Continuity — Sovereign Resilience-as-Code",
    description:
      "Cyber-physical continuity assurance for maritime corridors, NATO logistics, and defense supply chains.",
  },
  robots: { index: true, follow: true },
  alternates: { canonical: "/" },
};

export const viewport: Viewport = {
  themeColor: "#0a0e14",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

const GITHUB = "https://github.com/Hardonian/continuityos";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <header className="site-header">
          <Link href="/" className="brand" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
            <span>ContinuityOS</span>
            <span style={{ fontSize: "0.65rem", padding: "0.15rem 0.4rem", borderRadius: "3px", background: "rgba(14, 165, 233, 0.2)", color: "#38bdf8", border: "1px solid rgba(14, 165, 233, 0.4)", fontWeight: 700, letterSpacing: "0.05em" }}>SOVEREIGN DEFENSE</span>
          </Link>
          <SiteNav className="nav-desktop" />
          <a className="nav-github" href={GITHUB} target="_blank" rel="noreferrer">
            GitHub
          </a>
          <details className="nav-mobile">
            <summary aria-label="Open navigation menu">Menu</summary>
            <div className="nav-mobile-panel">
              <SiteNav className="nav-mobile-links" />
              <a
                className="nav-github"
                href={GITHUB}
                target="_blank"
                rel="noreferrer"
              >
                GitHub
              </a>
            </div>
          </details>
        </header>
        <main id="main">{children}</main>
        <footer className="site-footer">
          <SiteNav className="footer-nav" />
          <div className="footer-meta">
            <span>
              Aegis Continuity — Powered by the ContinuityOS Open-Core Engine.
            </span>
            <span className="muted">
              Advisory intelligence overlay. Human-in-the-loop. Never autonomous
              kinetic.
            </span>
            <span className="muted">
              © {new Date().getFullYear()} ContinuityOS. All rights reserved.
            </span>
          </div>
        </footer>
        <StructuredData />
      </body>
    </html>
  );
}
