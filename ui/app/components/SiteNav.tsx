import Link from "next/link";

const NAV = [
  { href: "/", label: "Platform" },
  { href: "/war-room", label: "War Room HUD" },
  { href: "/corridor-hub", label: "Global Corridors" },
  { href: "/allied-c2", label: "Allied C2 & CoT" },
  { href: "/canadian-corridors", label: "Sovereign Corridors" },
  { href: "/critical-minerals", label: "Critical Minerals" },
  { href: "/enterprise-connectors", label: "Enterprise Data" },
  { href: "/insurance-underwriting", label: "War-Risk & Ratings" },
  { href: "/rfp-proposal", label: "Government RFP / PBMM" },
  { href: "/sovereign-compliance", label: "ITSG-33 & SCIF" },
  { href: "/quantum-crypto", label: "PQC Envelopes" },
  { href: "/quickstart", label: "Quickstart" },
  { href: "/live", label: "Deployment" },
];

export default function SiteNav({ className }: { className?: string }) {
  return (
    <nav className={className} aria-label="Primary">
      {NAV.map((n) => (
        <Link key={n.href} href={n.href}>
          {n.label}
        </Link>
      ))}
    </nav>
  );
}
