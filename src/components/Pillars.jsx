import React, { useRef } from 'react';
import { Activity, Heart, Brain, Zap } from 'lucide-react';

const pillarsData = [
  {
    icon: <Activity size={24} />,
    title: 'Tělo',
    desc: 'Bio robot, zvyšování odolnosti, spánek, jóga a fyzická vyrovnanost.',
    items: ['Distres x eustres', 'Signalizační systém', 'Vyrovnaný jídelníček']
  },
  {
    icon: <Heart size={24} />,
    title: 'Emoce',
    desc: 'Pochopení a zpracování emocí, rodinné vztahy, práce s traumatem.',
    items: ['Saturace potřeb', 'Zvládání emocí', 'Identifikace vzorců']
  },
  {
    icon: <Brain size={24} />,
    title: 'Mysl',
    desc: 'Způsob myšlení, software bio robota, konflikty, očekávání a vliv.',
    items: ['Defragmentace', 'Konflikty a řešení', 'Autentické hodnoty']
  },
  {
    icon: <Zap size={24} />,
    title: 'Životní energie',
    desc: 'Palivo bio robota, dobíjení energie a signalizační systém únavy.',
    items: ['Zdroj energie', 'Co mě vyčerpává', 'Jak dobíjet energii']
  }
];

export default function Pillars() {
  return (
    <section id="pilire" className="section container">
      <div className="section-header">
        <h2 className="section-title">Čtyři základní pilíře</h2>
        <p className="section-desc">
          Celý koncept našich aktivit stojí na rozvoji a harmonii těchto čtyř tematických oblastí.
          Vše co děláme slouží k jejich podpoře.
        </p>
      </div>
      
      <div className="pillars-grid">
        {pillarsData.map((p, i) => (
          <PillarCard key={i} {...p} />
        ))}
      </div>
    </section>
  );
}

function PillarCard({ icon, title, desc, items }) {
  const cardRef = useRef(null);

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    cardRef.current.style.setProperty('--mouse-x', `${x}px`);
    cardRef.current.style.setProperty('--mouse-y', `${y}px`);
  };

  return (
    <div 
      className="pillar-card glass" 
      ref={cardRef} 
      onMouseMove={handleMouseMove}
    >
      <div className="pillar-icon">
        {icon}
      </div>
      <h3 className="pillar-title">{title}</h3>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', lineHeight: '1.5' }}>
        {desc}
      </p>
      <ul className="pillar-list">
        {items.map((it, i) => (
          <li key={i}>
            <span style={{ color: 'var(--accent-primary)', fontSize: '0.8rem' }}>•</span>
            {it}
          </li>
        ))}
      </ul>
    </div>
  );
}
