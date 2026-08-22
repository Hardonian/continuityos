export default function StructuredData() {
  const data = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": "https://aiautomatedsystems.ca/#org",
        name: "Aegis Continuity",
        url: "https://aiautomatedsystems.ca",
        sameAs: ["https://github.com/Hardonian/continuityos"],
      },
      {
        "@type": "SoftwareApplication",
        name: "Aegis Continuity",
        applicationCategory: "BusinessApplication",
        operatingSystem: "Linux, macOS, Windows, Docker",
        url: "https://aiautomatedsystems.ca",
        description:
          "Sovereign Resilience-as-Code and cyber-physical continuity assurance for critical maritime corridors, NATO logistics, Arctic operations, and defense supply chains.",
        offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
        author: { "@id": "https://aiautomatedsystems.ca/#org" },
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
