"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/", label: "Overview", icon: "⬡" },
  { href: "/checks", label: "All Checks", icon: "◈" },
  { href: "/flagged", label: "Flagged", icon: "⚑" },
  { href: "/eval", label: "Evaluation", icon: "◎" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="navbar">
      {/* Logo */}
      <div className="navbar-logo">
        <div className="navbar-logo-icon">⚖</div>
        <div>
          <div className="navbar-logo-text">LexGuard</div>
          <div className="navbar-logo-sub">Hallucination Monitor</div>
        </div>
      </div>

      {/* Navigation */}
      <div className="nav-section-label">Navigation</div>
      {NAV_LINKS.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={`nav-link ${pathname === link.href ? "active" : ""}`}
        >
          <span className="nav-link-icon">{link.icon}</span>
          {link.label}
        </Link>
      ))}

      {/* Footer */}
      <div className="nav-footer">
        <span className="nav-status-dot" />
        API Connected
        <div style={{ marginTop: 6 }}>LexGuard v0.1.0</div>
      </div>
    </nav>
  );
}
