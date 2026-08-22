import type { MetadataRoute } from "next";

export const dynamic = "force-static";

const BASE = "https://aiautomatedsystems.ca";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ["", "/capabilities", "/api", "/safety", "/quickstart", "/live"];
  const now = new Date();
  return routes.map((r) => ({
    url: `${BASE}${r}`,
    lastModified: now,
    changeFrequency: "monthly" as const,
    priority: r === "" ? 1 : 0.7,
  }));
}
