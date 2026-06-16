/**
 * components/layout/GlobalNav.tsx
 *
 * The persistent top navigation bar.
 * Mirrors Apple's 44px true-black global-nav design.
 */

export default function GlobalNav() {
  return (
    <nav className="global-nav" role="navigation" aria-label="Global">
      <div className="global-nav__inner">
        {/* Logo / brand */}
        <span className="global-nav__brand">⬡ Crawler</span>

        {/* Right-aligned links */}
        <div className="global-nav__links">
          <a href="#ingest" className="global-nav__link">Ingest</a>
          <a href="#chat" className="global-nav__link">Chat</a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="global-nav__link"
          >
            API Docs
          </a>
        </div>
      </div>
    </nav>
  );
}
