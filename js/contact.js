document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('main-contact-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Odesílám...';
    submitBtn.disabled = true;

    // Odstranění předchozí hlášky, pokud existuje
    const existingMsg = document.getElementById('contact-status-msg');
    if (existingMsg) existingMsg.remove();

    const data = {
      access_key: "8527d713-f331-42ac-93f6-a22905d1380c",
      subject: "Nová zpráva z webu motivus.cz",
      from_name: "Motivus Form",
      name: form.name.value,
      email: form.email.value,
      message: form.message.value
    };

    try {
      // Odeslání přes službu Web3Forms přímo z prohlížeče
      const response = await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      const msgDiv = document.createElement('div');
      msgDiv.id = 'contact-status-msg';
      msgDiv.style.marginTop = 'var(--space-md)';
      msgDiv.style.padding = 'var(--space-sm)';
      msgDiv.style.borderRadius = 'var(--radius-md)';
      msgDiv.style.textAlign = 'center';
      msgDiv.style.transition = 'opacity 0.5s ease';
      
      if (response.ok && result.success) {
        msgDiv.style.backgroundColor = 'rgba(46, 204, 113, 0.1)';
        msgDiv.style.color = '#2ecc71';
        msgDiv.style.border = '1px solid rgba(46, 204, 113, 0.3)';
        msgDiv.textContent = 'Zpráva byla úspěšně odeslána. Brzy se vám ozveme!';
        form.reset(); // Vyprázdnění formuláře
      } else {
        throw new Error(result.message || 'Neznámá chyba při komunikaci se serverem.');
      }

      form.appendChild(msgDiv);

    } catch (error) {
      const msgDiv = document.createElement('div');
      msgDiv.id = 'contact-status-msg';
      msgDiv.style.marginTop = 'var(--space-md)';
      msgDiv.style.padding = 'var(--space-sm)';
      msgDiv.style.borderRadius = 'var(--radius-md)';
      msgDiv.style.backgroundColor = 'rgba(231, 76, 60, 0.1)';
      msgDiv.style.color = '#e74c3c';
      msgDiv.style.border = '1px solid rgba(231, 76, 60, 0.3)';
      msgDiv.style.textAlign = 'center';
      msgDiv.style.transition = 'opacity 0.5s ease';
      msgDiv.textContent = 'Chyba odesílání: ' + error.message;
      
      form.appendChild(msgDiv);
    } finally {
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;

      // Zpráva postupně zmizí po 7 sekundách
      setTimeout(() => {
        const msg = document.getElementById('contact-status-msg');
        if (msg) {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        }
      }, 7000);
    }
  });
});
