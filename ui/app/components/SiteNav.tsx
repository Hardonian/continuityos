import Link from "next/link";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/capabilities", label: "Capabilities" },
  { href: "/api", label: "API" },
  { href: "/safety", label: "Safety & ROE" },
  { href: "/quickstart", label: "Quickstart" },
  { href: "/live", label: "Live Deployment" },
  { href: "/cop-dashboard.html", label: "COP Dashboard" },
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
