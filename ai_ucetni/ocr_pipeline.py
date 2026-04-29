"""
Motivus AI Účetní — GPT-4o Vision OCR Pipeline
Extracts structured data from receipt/invoice photos.
"""
import os
import base64
import json
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ──────────────── Pydantic Schema ────────────────


class ExtractedReceipt(BaseModel):
    """Structured data extracted from a receipt/invoice photo."""
    vendor_name: str = Field(description="Nazev dodavatele (obchod, firma)")
    vendor_ico: Optional[str] = Field(None, description="ICO dodavatele, pokud je na dokladu")
    date: str = Field(description="Datum na dokladu ve formatu YYYY-MM-DD")
    total_amount: float = Field(description="Celkova castka v CZK")
    vat_amount: Optional[float] = Field(0, description="Castka DPH, pokud je uvedena")
    category: str = Field(description="Kategorie vydaje: elektronika, doprava, vzdelavani, kancelar, zdravi, potraviny, sluzby, pronjem, marketing, ostatni")
    description: str = Field(description="Kratky popis polozek na uctence (max 100 znaku)")
    payment_method: str = Field("card", description="Zpusob platby: hotove, kartou, prevodem")
    is_deductible: bool = Field(True, description="Lze uplatnit jako danove uznatelny vydaj pro OSVC?")
    confidence: float = Field(description="Mira jistoty extrakce 0.0 az 1.0")
    raw_text: str = Field(description="Surovy text precteny z dokladu")


SYSTEM_PROMPT = """Jsi cesky danovy asistent specializovany na OSVC (neplatce DPH).
Analyzuj prilozenou fotku uctenky, faktury nebo paragonu a extrahuj strukturovana data.

PRAVIDLA:
1. Vsechny castky prevadej na CZK. Pokud je castka v jine mene, prepocitej odhadem.
2. Datum vzdy ve formatu YYYY-MM-DD.
3. Kategorie vyber z: elektronika, doprava, vzdelavani, kancelar, zdravi, potraviny, sluzby, pronajem, marketing, ostatni
4. is_deductible = true pokud je vydaj danove uznatelny pro OSVC (napr. pracovni nastroje, vzdelavani).
   is_deductible = false pro osobni vydaje (jidlo v restauraci bez obchodniho ucelu, obleceni atd.)
5. confidence = tvoje jistota ze jsi spravne precetl data (0.0 = nic nevidim, 1.0 = jiste)
6. Pokud nemuzes precist neco, odhadni nejlepsi moznou hodnotu a sniz confidence.

Odpovez POUZE validnim JSON podle daneho schematu, zadny dalsi text."""


def encode_image(image_path: str) -> str:
    """Encode image to base64 for API."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_receipt(image_path: str, model: str = "gpt-4o-mini") -> ExtractedReceipt:
    """
    Extract structured data from a receipt image using GPT-4o Vision.
    
    Args:
        image_path: Path to the receipt image file
        model: OpenAI model to use (gpt-4o-mini is cheapest, gpt-4o for complex receipts)
    
    Returns:
        ExtractedReceipt with structured data
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    base64_image = encode_image(image_path)
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyzuj tuto uctenku a extrahuj data:"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=1000,
        temperature=0.1,
    )
    
    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)
    
    return ExtractedReceipt(**data)


def extract_receipt_from_base64(image_b64: str, mime_type: str = "image/jpeg",
                                 model: str = "gpt-4o-mini") -> ExtractedReceipt:
    """Extract from base64-encoded image (for WhatsApp/email integration)."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyzuj tuto uctenku a extrahuj data:"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_b64}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=1000,
        temperature=0.1,
    )
    
    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)
    
    return ExtractedReceipt(**data)


def format_receipt(receipt: ExtractedReceipt) -> str:
    """Format extracted receipt as a readable confirmation message."""
    deductible = "ANO" if receipt.is_deductible else "NE (osobni vydaj)"
    lines = [
        f"Dodavatel:  {receipt.vendor_name}",
        f"Datum:      {receipt.date}",
        f"Castka:     {receipt.total_amount:,.0f} Kc",
    ]
    if receipt.vat_amount:
        lines.append(f"DPH:        {receipt.vat_amount:,.0f} Kc")
    lines.extend([
        f"Kategorie:  {receipt.category}",
        f"Popis:      {receipt.description}",
        f"Platba:     {receipt.payment_method}",
        f"Uznatelne:  {deductible}",
        f"Jistota:    {receipt.confidence:.0%}",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr_pipeline.py <image_path>")
        print("  Extracts structured data from a receipt photo using GPT-4o Vision.")
        sys.exit(1)
    
    image_path = sys.argv[1]
    print(f"Processing: {image_path}")
    print("-" * 40)
    
    try:
        receipt = extract_receipt(image_path)
        print(format_receipt(receipt))
        print("-" * 40)
        print(f"Raw JSON: {receipt.model_dump_json(indent=2)}")
    except Exception as e:
        print(f"[ERROR] {e}")
