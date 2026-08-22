import Link from "next/link";

export default function NotFound() {
  return (
    <div>
      <p className="eyebrow">404</p>
      <h1>Page not found</h1>
      <p className="tagline">
        The page you requested is not part of this reference surface.
      </p>
      <div className="hero-actions">
        <Link href="/" className="btn btn-primary">
          Return home
        </Link>
        <Link href="/capabilities" className="btn btn-ghost">
          View capabilities
        </Link>
      </div>
    </div>
  );
}
