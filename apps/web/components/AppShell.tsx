'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const nav = [
  ['/platform', 'Platform'],
  ['/', 'Command'],
  ['/facilities', 'Facilities'],
  ['/assets', 'Assets'],
  ['/missions', 'Missions'],
  ['/review', 'Evidence'],
  ['/coverage', 'Coverage'],
  ['/mlops', 'MLOps'],
  ['/reports', 'Reports'],
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">OI</div>
          <div><strong>OpenInspect</strong><span>OS / Integrity Control</span></div>
        </div>
        <nav>
          {nav.map(([href, label]) => (
            <Link key={href} href={href} className={path === href ? 'active' : ''}>
              <span className="nav-led" />{label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div><span className="status-dot online" />API connected</div>
          <small>Project-owned demo data</small>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div>
            <span className="eyebrow">ASSET INTEGRITY OPERATIONS</span>
            <h1>{nav.find(([href]) => href === path)?.[1] ?? 'Workspace'}</h1>
          </div>
          <div className="topbar-meta"><span>UTC</span><strong>LIVE DEMO</strong></div>
        </header>
        {children}
      </main>
    </div>
  );
}
