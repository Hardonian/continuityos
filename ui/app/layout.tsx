import type { ReactNode } from "react";
import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "./globals.css";
import SiteNav from "./components/SiteNav";
import StructuredData from "./components/StructuredData";

export const metadata: Metadata = {
  metadataBase: new URL("https://aiautomatedsystems.ca"),
  title: {
    default: "Aegis Continuity — Sovereign Resilience-as-Code",
    template: "%s — Aegis Continuity",
  },
  description:
    "Sovereign Resilience-as-Code and cyber-physical continuity assurance for critical maritime corridors, NATO logistics, Arctic operations, and defense supply chains. Powered by the ContinuityOS Open-Core Engine.",
  applicationName: "Aegis Continuity",
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
  ],
  openGraph: {
    type: "website",
    siteName: "Aegis Continuity",
    title: "Aegis Continuity — Sovereign Resilience-as-Code",
    description:
      "Sovereign Resilience-as-Code and cyber-physical continuity assurance for critical maritime corridors, NATO logistics, and defense supply chains.",
    url: "https://aiautomatedsystems.ca",
  },
  twitter: {
    card: "summary_large_image",
    title: "Aegis Continuity — Sovereign Resilience-as-Code",
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
          <Link href="/" className="brand">
            Aegis Continuity
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
