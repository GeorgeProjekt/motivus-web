import React, { useEffect } from 'react';
import { ChevronRight } from 'lucide-react';

export default function Hero() {
  return (
    <section className="hero">
      <div className="hero-bg-glow"></div>
      <div className="container" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '4rem', alignItems: 'center' }}>
        <div style={{ textAlign: 'left' }}>
          <h1 className="hero-title" style={{ fontSize: 'clamp(2.5rem, 5vw, 4.5rem)' }}>
            Smysluplný čas. <br />
            <span className="text-gradient">Vnitřní harmonie.</span>
          </h1>
          <p className="hero-subtitle" style={{ marginInline: '0', maxWidth: '100%' }}>
            Vytváříme bezpečný prostor, kde se můžete zastavit, zorientovat a znovu se spojit se svou přirozenou silou.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-start', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={() => document.getElementById('poslitodal').scrollIntoView({ behavior: 'smooth' })}>
              Klub "Pošli to dál" <ChevronRight size={20} />
            </button>
            <button className="btn btn-outline" onClick={() => document.getElementById('pilire').scrollIntoView({ behavior: 'smooth' })}>
              Koncept 4 Pilířů
            </button>
          </div>
        </div>
        <div style={{ position: 'relative' }}>
          <div style={{ position: 'absolute', inset: '-10%', background: 'var(--glow)', filter: 'blur(60px)', opacity: 0.4, zIndex: -1 }}></div>
          <img src="/motivus_zena_02.png" alt="Motivus Vize" style={{ width: '100%', borderRadius: '2rem', boxShadow: '0 20px 40px rgba(0,0,0,0.5)', border: '1px solid rgba(255,255,255,0.05)' }} />
        </div>
      </div>
    </section>
  );
}
