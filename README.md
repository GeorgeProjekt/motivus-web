# Motivus Web Application

Tento repozitář obsahuje webovou a backendovou infrastrukturu projektu **Motivus**. 

## 🚀 Komponenty

1. **Frontend (React + Vite + TailwindCSS)**
   - Prezentační Single Page Aplikace (SPA) pro značku Motivus.
   - Integrace s rezervačním systémem **Cal.com**.
   - Moderní animace, Glassmorphism design a responzivní rozhraní.

2. **Backend: Platební brána & Fakturace (`/billing/`)**
   - **Stripe Webhook Server** (`webhook_server.py`) - zachytává úspěšné platby z Cal.com / Stripe v měně CZK.
   - **Fakturoid Integrace** (`fakturoid_client.py`) - automaticky vystavuje faktury zákazníkům přes API v3 po přijetí platby a odesílá je e-mailem.

3. **AI Účetní Engine (`/ai_ucetni/`)**
   - Automatizovaný systém pro OSVČ v týmu Motivus.
   - Obsahuje daňový kalkulátor pro rok 2026 (porovnává výhodnost paušální daně vs. skutečných výdajů).
   - **GPT-4o Vision OCR:** Skript `ocr_pipeline.py` umožňuje naskenovat vyfocenou účtenku a automaticky z ní extrahovat strukturovaná data (DPH, IČO, částku a kategorii) do SQLite databáze.

## ⚙️ Spuštění a Vývoj

**Požadavky:**
- Node.js & npm (pro frontend)
- Python 3.10+ (pro webhooky a AI účetního)

### Frontend
```bash
npm install
npm run dev
```

### Backend (Stripe Webhook + Fakturoid)
Ujistěte se, že máte `.env` soubor s vyplněnými klíči (`STRIPE_SECRET_KEY`, `FAKTUROID_CLIENT_ID`, atd.).
```bash
pip install -r requirements.txt  # pokud existuje
python billing/webhook_server.py
```
*Server běží lokálně na portu 4242.*

### AI Účetní
```bash
python ai_ucetni/main.py init
python ai_ucetni/main.py status
```

---
*Vytvořeno pro tým Motivus (2026).*
