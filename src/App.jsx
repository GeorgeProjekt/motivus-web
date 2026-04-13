import React from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Pillars from './components/Pillars';
import ProjectCTA from './components/ProjectCTA';
import Values from './components/Values';
import './App.css'; // empty

function App() {
  return (
    <div style={{ position: 'relative', overflowX: 'hidden' }}>
      <Navbar />
      <main>
        <Hero />
        
        {/* Decorative background element */}
        <div style={{ position: 'absolute', top: '150vh', right: '-10vw', width: '50vw', height: '50vw', background: 'radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 60%)', filter: 'blur(80px)', zIndex: -1 }}></div>

        <Pillars />
        <ProjectCTA />
        
        {/* Decorative background element */}
        <div style={{ position: 'absolute', bottom: '10vh', left: '-10vw', width: '60vw', height: '60vw', background: 'radial-gradient(circle, rgba(16, 185, 129, 0.05) 0%, transparent 60%)', filter: 'blur(80px)', zIndex: -1 }}></div>

        <Values />
      </main>
      <footer>
        <div className="container">
          <p>&copy; {new Date().getFullYear()} Sdružení Motivus. Všechna práva vyhrazena.</p>
          <p style={{ marginTop: '0.5rem', opacity: 0.5 }}>Tento web je konceptuálním návrhem vygenerovaným umělou inteligencí Antigravity.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
