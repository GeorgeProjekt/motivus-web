/* Theme Manager — Dark/Light mode */
class ThemeManager {
  constructor() {
    this.root = document.documentElement;
    this.toggleBtn = document.getElementById('theme-toggle');
    this.icon = this.toggleBtn?.querySelector('.theme-icon');
    this.init();
  }

  init() {
    // Check saved preference or system preference
    const saved = localStorage.getItem('motivus-theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      this.setDark();
    } else {
      this.setLight();
    }

    // Listen for toggle
    this.toggleBtn?.addEventListener('click', () => this.toggle());

    // Listen for system changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('motivus-theme')) {
        e.matches ? this.setDark() : this.setLight();
      }
    });
  }

  toggle() {
    this.root.classList.contains('dark-mode') ? this.setLight() : this.setDark();
  }

  setDark() {
    this.root.classList.add('dark-mode');
    localStorage.setItem('motivus-theme', 'dark');
    if (this.icon) this.icon.textContent = '☀';
  }

  setLight() {
    this.root.classList.remove('dark-mode');
    localStorage.setItem('motivus-theme', 'light');
    if (this.icon) this.icon.textContent = '☽';
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.themeManager = new ThemeManager();
});
