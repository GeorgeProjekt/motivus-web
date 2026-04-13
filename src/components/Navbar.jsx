import React from 'react';
import { Menu } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className="navbar glass">
      <div className="container nav-content">
        <div className="logo" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <img src="/logo.jpeg" alt="Motivus Logo" style={{ width: '36px', height: '36px', borderRadius: '50%', border: '2px solid var(--accent-primary)' }} />
          <span className="text-gradient">MOTIVUS</span>
        </div>
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
          <a href="#pilire" style={{ color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.95rem' }}>4 Pilíře</a>
          <a href="#poslitodal" style={{ color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.95rem' }}>Pošli to dál</a>
          <a href="#hodnoty" style={{ color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.95rem' }}>Hodnoty</a>
          <button className="btn btn-outline" style={{ padding: '0.5rem 1rem' }}>
            <Menu size={20} />
          </button>
        </div>
      </div>
    </nav>
  );
}
