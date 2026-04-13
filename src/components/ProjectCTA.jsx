import React from 'react';
import { Users, Droplet, MoveRight } from 'lucide-react';

export default function ProjectCTA() {
  return (
    <section id="poslitodal" className="section container">
      <div className="cta-box" style={{ padding: '4rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '3rem', alignItems: 'center', textAlign: 'left' }}>
        <div>
          <h2 className="section-title" style={{ marginBottom: '0.5rem' }}>Klub "Pošli to dál"</h2>
          <p className="section-desc" style={{ marginBottom: '2.5rem', fontFamily: 'var(--font-heading)', fontSize: '1.25rem', marginInline: '0', color: 'var(--accent-secondary)' }}>
            „Dostal jsi hodnotu? Pošli to dál.“
          </p>

          <div style={{ color: 'var(--text-secondary)' }}>
            <p style={{ marginBottom: '1rem' }}>
              Naším klíčovým projektem je komunitní klub, který nám umožňuje dlouhodobě podporovat a rozšiřovat aktivity našeho sdružení na území Moravskoslezského kraje.
            </p>
            <p style={{ marginBottom: '2.5rem' }}>
              Zakládáme ekosystém navzájem se rozvíjejících lidí. Nejedná se o terapii ani prázdnou ezo-záležitost, ale o reálné budování pevných vztahů a odpovědnosti, prostřednictvím drobných pravidelných příspěvků členů, se kterými pak společně rosteme.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-start', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" style={{ background: 'var(--accent-secondary)' }}>
              Chci se přidat <MoveRight size={20} />
            </button>
            <button className="btn btn-outline" style={{ borderColor: 'rgba(255,255,255,0.2)' }}>
              Jak to funguje
            </button>
          </div>
        </div>
        <div style={{ position: 'relative' }}>
          <img src="/motivus_par_01.png" alt="Otevřený rozhovor" style={{ width: '100%', borderRadius: '1.5rem', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }} />
        </div>
      </div>
    </section>
  );
}
