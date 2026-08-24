import Link from "next/link";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/war-room", label: "War Room HUD" },
  { href: "/critical-minerals", label: "Critical Minerals" },
  { href: "/canadian-corridors", label: "Canadian Corridors" },
  { href: "/supply-chain", label: "Supply Chain BOM" },
  { href: "/counter-intel", label: "Counter-Intel / EMCON" },
  { href: "/environmental-risk", label: "Environmental & Permafrost" },
  { href: "/cluster-mesh", label: "SCIF Cluster Mesh" },
  { href: "/quantum-crypto", label: "PQC / ZKP Crypto" },
  { href: "/rbac-audit", label: "RBAC & Tenancy" },
  { href: "/scif-attestation", label: "SCIF Attestation" },
  { href: "/rfp-proposal", label: "Gov RFP / PBMM" },
  { href: "/sovereign-compliance", label: "Sovereign Compliance" },
  { href: "/capabilities", label: "Capabilities" },
  { href: "/api", label: "API" },
  { href: "/safety", label: "Safety & ROE" },
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
