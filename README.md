# Motivus Web Application & AI Účetní

Tento repozitář obsahuje kompletní frontendovou prezentaci a backendovou architekturu pro projekt **Motivus**, včetně komplexního systému "AI Účetní" pro automatizaci financí a fakturace.

## 🚀 Architektura a Komponenty

Systém je rozdělen do tří hlavních částí:

### 1. Frontend (React / Vanilla JS)
- Webová prezentace s integrací rezervačního systému **Cal.com**.
- Mobilní administrativní aplikace **Backstage** (`backstage.html`), která funguje jako kapesní AI Účetní. Chráněna PIN kódem. 

### 2. Platební a rezervační pipeline (Stripe + Fakturoid)
- Zákazník platí zálohu za sezení přes Cal.com, což je procesováno službou **Stripe**.
- Stripe Webhook Server (`billing/webhook_server.py`) zachytává událost `payment_intent.succeeded`.
- **Dvoufázové fakturování:** Webhook ihned po platbě zálohy **nevystavuje** fakturu. Místo toho zapíše událost do databáze jako "Čekající sezení" (Pending Session).
- Po reálném proběhnutí sezení obsluha v aplikaci `backstage.html` klikne na "Vystavit fakturu". V tu chvíli se volá **Fakturoid API v3**, které odečte zaplacenou zálohu a odešle klientovi konečnou fakturu. Pokud klient nedorazí, lze sezení "Stornovat" bez vystavení faktury.

### 3. AI Účetní Backend (FastAPI + SQLite + OpenAI)
- Adresář `/ai_ucetni/`.
- **FastAPI server** (`api.py`) obsluhuje mobilní aplikaci. Zajišťuje upload účtenek, listing čekajících sezení a povely k fakturaci. Vše chráněno HTTP Basic Auth.
- **GPT-4o Vision OCR** (`ocr_pipeline.py`) - po uploadu vyfocené účtenky se pomocí AI vytěží data (Dodavatel, Částka, Kategorie) a ihned se propíší do SQLite databáze.
- **Daňový kalkulátor 2026** - při každé akci (nový příjem, nová účtenka) systém real-time porovnává výhodnost placení daní formou *Výdajového paušálu* vs. *Skutečných výdajů* a doporučuje výhodnější variantu s přesným vyčíslením úspory.

---

## ⚙️ Produkční prostředí (Forpsi VPS)

Systém běží na Forpsi Linux VPS, s nasazeným reverzním proxy serverem **Nginx** a SSL certifikátem (Let's Encrypt) na subdoméně `api.motivus.cz`.

### Nginx Konfigurace
- `https://api.motivus.cz/backstage.html` -> Vstup do mobilní aplikace.
- `https://api.motivus.cz/api/*` -> Směřováno na FastAPI (`127.0.0.1:8000`).
- `https://api.motivus.cz/webhook` -> Směřováno na Stripe Webhook server (`127.0.0.1:4242`).

### Správa procesů na serveru
Běží na pozadí pomocí `nohup`:
1. **API Server:** 
   ```bash
   cd /var/www/motivus-web/ai_ucetni
   nohup python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 > ../api.log 2>&1 &
   ```
2. **Webhook Server:** 
   ```bash
   cd /var/www/motivus-web
   nohup python3 billing/webhook_server.py > webhook.log 2>&1 &
   ```

---

## 🔑 Environmentální proměnné (`.env`)

K běhu jsou naprosto nezbytné následující klíče v souboru `.env`:

```env
# === FAKTUROID ===
FAKTUROID_SLUG=...
FAKTUROID_CLIENT_ID=...
FAKTUROID_CLIENT_SECRET=...

# === STRIPE ===
# Hlavní API klíč (z Developers -> API keys). Slouží pro dotazování se na Stripe.
STRIPE_SECRET_KEY=sk_live_...
# Klíč pro webhook (z Developers -> Webhooks). Slouží k ověření pravosti příchozích zpráv od Stripe.
STRIPE_WEBHOOK_SECRET=whsec_...

# === OPENAI ===
# Klíč pro čtení vyfocených účtenek pomocí GPT-4o
OPENAI_API_KEY=sk-...
```

## 🔐 Přístupy
- **Backstage aplikace (PIN):** `2026`
- **API Basic Auth (Backend):** Uživatelské jméno: `motivus`, Heslo: `robot2026`

---
*Vytvořeno automatizovaně AI asistentem pro tým Motivus (2026).*
