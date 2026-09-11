export default function StructuredData() {
  const data = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": "https://continuityos.com/#org",
        name: "ContinuityOS / Aegis Continuity",
        url: "https://continuityos.com",
        sameAs: ["https://github.com/Hardonian/continuityos"],
      },
      {
        "@type": "SoftwareApplication",
        name: "ContinuityOS",
        applicationCategory: "SecurityApplication, BusinessApplication",
        operatingSystem: "Linux, macOS, Windows, Docker, Air-Gapped Bare Metal",
        url: "https://continuityos.com",
        description:
          "Sovereign Resilience-as-Code and cyber-physical continuity assurance for critical maritime corridors, NATO logistics, Arctic operations, and defense supply chains.",
        offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
        author: { "@id": "https://continuityos.com/#org" },
      },
    ],
  };
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}
