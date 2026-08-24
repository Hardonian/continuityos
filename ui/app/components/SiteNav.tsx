import Link from "next/link";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/canadian-corridors", label: "Canadian Corridors" },
  { href: "/supply-chain", label: "Supply Chain BOM" },
  { href: "/rfp-proposal", label: "Gov RFP / PBMM" },
  { href: "/sovereign-compliance", label: "Sovereign Compliance" },
  { href: "/capabilities", label: "Capabilities" },
  { href: "/api", label: "API" },
  { href: "/safety", label: "Safety & ROE" },
  { href: "/cop-dashboard.html", label: "Tactical HUD" },
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
