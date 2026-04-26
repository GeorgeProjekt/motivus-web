/**
 * MOTIVUS - Cookie Consent Logic
 */
(function() {
  const cookieBanner = document.getElementById('cookie-banner');
  const acceptBtn = document.getElementById('cookie-accept');

  // Check if consent is already given
  const hasConsent = localStorage.getItem('motivus_cookie_consent');

  if (!hasConsent && cookieBanner) {
    // Show banner after a slight delay for better UX
    setTimeout(() => {
      cookieBanner.classList.add('show');
    }, 1000);
  }

  // Handle click on "Rozumím a přijímám"
  if (acceptBtn) {
    acceptBtn.addEventListener('click', () => {
      // Save consent to localStorage
      localStorage.setItem('motivus_cookie_consent', 'true');
      
      // Hide banner
      cookieBanner.classList.remove('show');
      
      // Optionally remove from DOM after transition
      setTimeout(() => {
        cookieBanner.style.display = 'none';
      }, 500);
    });
  }
})();
