/* Navigation — mobile toggle */
class NavManager {
  constructor() {
    this.hamburger = document.querySelector('.nav-hamburger');
    this.links = document.querySelector('.nav-links');
    this.init();
  }

  init() {
    this.hamburger?.addEventListener('click', () => {
      this.links?.classList.toggle('open');
      this.hamburger.classList.toggle('active');
    });

    // Close on link click
    this.links?.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        this.links.classList.remove('open');
        this.hamburger?.classList.remove('active');
      });
    });
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.navManager = new NavManager();
});
