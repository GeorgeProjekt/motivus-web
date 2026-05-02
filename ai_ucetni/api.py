import os
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import secrets
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ocr_pipeline import extract_receipt
from database import (init_db, add_expense, get_income_ytd, get_expenses_ytd, 
                      get_pending_sessions, get_session, mark_session_invoiced, 
                      mark_session_cancelled, add_income, get_provider)
from tax_calculator import compare_strategies
from billing.fakturoid_client import get_or_create_contact, create_invoice
import shutil
from datetime import datetime

app = FastAPI(title="Motivus AI Účetní API")

# Povolíme CORS pro frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # V produkci omezit na localhost a motivus.cz
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

# Zabezpečení pomocí HTTP Basic Auth
def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "motivus")
    correct_password = secrets.compare_digest(credentials.password, "robot2026")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nesprávné jméno nebo heslo",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/api/status")
def get_status(username: str = Depends(verify_credentials)):
    """Vrací aktuální daňový přehled."""
    # Získáme data pro Jiřího (provider_id = 1)
    income = get_income_ytd(1)
    expenses = get_expenses_ytd(1)
    
    # Vypočítáme daň (vedlejší činnost OSVČ)
    taxes = compare_strategies(income, expenses, activity_type="volna", is_main_activity=False)
    
    return {
        "status": "ok",
        "taxes": taxes
    }

@app.post("/api/upload")
async def upload_receipt(file: UploadFile = File(...), username: str = Depends(verify_credentials)):
    """Přijme fotku účtenky, zpracuje přes GPT-4o a uloží."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nebyl nahrán žádný soubor.")
        
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Voláme náš existující OCR engine
        receipt_data = extract_receipt(file_path)
        
        # Uložíme do DB
        add_expense(
            provider_id=1, # Default Jiří
            amount=receipt_data.total_amount,
            description=f"{receipt_data.vendor_name} - {receipt_data.purpose}",
            category=receipt_data.category,
            is_tax_deductible=receipt_data.is_tax_deductible
        )
        
        # Smažeme dočasný soubor fotky
        os.remove(file_path)
        
        return {
            "status": "success",
            "extracted_data": receipt_data.model_dump()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pending-sessions")
def list_pending_sessions(username: str = Depends(verify_credentials)):
    """Vrací čekající sezení, která ještě nebyla fakturována."""
    sessions = get_pending_sessions()
    return {"sessions": sessions}

@app.post("/api/sessions/{session_id}/invoice")
def invoice_session(session_id: int, username: str = Depends(verify_credentials)):
    """Vygeneruje finální fakturu ve Fakturoidu pro dané sezení."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sezení nenalezeno")
    if session['status'] == 'invoiced':
        raise HTTPException(status_code=400, detail="Faktura již byla vystavena")

    provider = get_provider(session['provider_id'])
    
    try:
        # 1. Kontakt ve Fakturoidu
        contact = get_or_create_contact(
            name=session['client_name'] or session['client_email'].split("@")[0],
            email=session['client_email'],
            phone=session['client_phone'],
        )
        
        # 2. Vystavení faktury (s odečtenou zálohou)
        invoice = create_invoice(
            contact_id=contact["id"],
            service_name=session["service_name"],
            total_price=session["total_price"],
            deposit_paid=session["deposit_paid"],
            provider_name=provider["name"] if provider else "Mgr. Jiří Synek",
            provider_ico=provider["ico"] if provider else "24400505",
            note=f"Záloha zaplacena online: {session['stripe_intent_id']}"
        )
        
        # 3. Označení v DB a přidání příjmu
        mark_session_invoiced(session_id)
        
        add_income(
            provider_id=session['provider_id'],
            amount=session['total_price'], # Do účetnictví se počítá celková částka
            date_str=datetime.now().strftime("%Y-%m-%d"),
            source="stripe_invoice",
            client_name=session['client_name'],
            service_name=session['service_name'],
            invoice_id=str(invoice['id'])
        )
        
        return {"status": "success", "invoice_id": invoice['id']}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při vystavování faktury: {str(e)}")

@app.post("/api/sessions/{session_id}/cancel")
def cancel_session(session_id: int, username: str = Depends(verify_credentials)):
    """Stornuje čekající sezení, faktura se nevystaví."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sezení nenalezeno")
    if session['status'] != 'pending':
        raise HTTPException(status_code=400, detail="Lze stornovat jen čekající sezení")
        
    mark_session_cancelled(session_id)
    return {"status": "success", "message": "Sezení bylo stornováno."}

if __name__ == "__main__":
    import uvicorn
    # Spustí server na portu 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
