import os
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import secrets
from ocr_pipeline import extract_receipt
from database import init_db, add_expense, get_income_ytd, get_expenses_ytd
from tax_calculator import compare_strategies
import shutil

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

if __name__ == "__main__":
    import uvicorn
    # Spustí server na portu 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
