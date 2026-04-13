/* Scroll Reveal + Nav effects */
class ScrollManager {
  constructor() {
    this.nav = document.querySelector('.nav');
    this.reveals = document.querySelectorAll('.reveal');
    this.init();
  }

  init() {
    // Intersection Observer for reveals
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });

    this.reveals.forEach(el => observer.observe(el));

    // Nav scroll effect
    window.addEventListener('scroll', () => {
      if (this.nav) {
        this.nav.classList.toggle('scrolled', window.scrollY > 50);
      }
    }, { passive: true });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(anchor.getAttribute('href'));
        if (target) {
          const offset = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-height')) || 72;
          window.scrollTo({
            top: target.offsetTop - offset,
            behavior: 'smooth'
          });
          // Close mobile nav if open
          document.querySelector('.nav-links')?.classList.remove('open');
        }
      });
    });
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.scrollManager = new ScrollManager();
});
