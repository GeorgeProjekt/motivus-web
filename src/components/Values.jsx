import React from 'react';
import { Star, Shield, HandHeart, Sparkles } from 'lucide-react';

const values = [
  {
    icon: <Star size={32} />,
    title: 'Jedinečnost & Autenticita',
    desc: 'Nehodnotíme. Respektujeme osobní tempo a hranice. Jsme opravdoví.'
  },
  {
    icon: <Shield size={32} />,
    title: 'Bezpečí & Důvěra',
    desc: 'Prostor absolutní svobody projevu bez tlaku na výkon či společenské role.'
  },
  {
    icon: <HandHeart size={32} />,
    title: 'Vědomá práce s emocemi',
    desc: 'Emoce nejsou problém, ale zdroj důležitých informací pro kvalitní život.'
  },
  {
    icon: <Sparkles size={32} />,
    title: 'Jemnost je síla',
    desc: 'Celostní přístup a laskavost je u nás považována za hlavní zdroj rozvoje.'
  }
];

export default function Values() {
  return (
    <section id="hodnoty" className="section container">
      <div className="section-header">
        <h2 className="section-title">Náš Manifest a Hodnoty</h2>
        <p className="section-desc">
          Odmítáme rychlá povrchní řešení. Nevnucujeme univerzální návody. Přebíráme zodpovědnost a budujeme stabilitu na reálném vnitřním klidu.
        </p>
      </div>

      <div className="values-grid">
        {values.map((v, i) => (
          <div key={i} className="value-item glass" style={{ padding: '2rem', borderRadius: '1rem', border: '1px solid rgba(255,255,255,0.02)' }}>
            <div className="value-icon">
              {v.icon}
            </div>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.75rem' }}>{v.title}</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
              {v.desc}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
