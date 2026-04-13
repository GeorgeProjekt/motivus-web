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
      name: form.name.value,
      email: form.email.value,
      message: form.message.value
    };

    try {
      // Odeslání na náš nový vlastní VPS endpoint
      const response = await fetch('https://podpis.motivus.cz/contact.php', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
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
      
      if (response.ok && result.status === 'success') {
        msgDiv.style.backgroundColor = 'rgba(46, 204, 113, 0.1)';
        msgDiv.style.color = '#2ecc71';
        msgDiv.style.border = '1px solid rgba(46, 204, 113, 0.3)';
        msgDiv.textContent = result.message || 'Zpráva byla úspěšně odeslána!';
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
