import type { MetadataRoute } from "next";

export const dynamic = "force-static";

const BASE = process.env.NEXT_PUBLIC_APP_URL || "https://continuityos.com";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = [
    "",
    "/war-room",
    "/canadian-corridors",
    "/critical-minerals",
    "/corridor-hub",
    "/allied-c2",
    "/enterprise-connectors",
    "/insurance-underwriting",
    "/procurement",
    "/rfp-proposal",
    "/sovereign-compliance",
    "/scif-attestation",
    "/quantum-crypto",
    "/cluster-mesh",
    "/counter-intel",
    "/environmental-risk",
    "/supply-chain",
    "/rbac-audit",
    "/capabilities",
    "/api",
    "/safety",
    "/quickstart",
    "/live",
  ];
  const now = new Date();
  return routes.map((r) => ({
    url: `${BASE}${r}`,
    lastModified: now,
    changeFrequency: "monthly" as const,
    priority: r === "" ? 1 : 0.8,
  }));
}

