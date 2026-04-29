"""
Fakturoid API v3 Client for Motivus
Uses OAuth2 Client Credentials Flow
Docs: https://www.fakturoid.cz/api/v3
"""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SLUG = os.getenv("FAKTUROID_SLUG", "jirisynek1")
CLIENT_ID = os.getenv("FAKTUROID_CLIENT_ID")
CLIENT_SECRET = os.getenv("FAKTUROID_CLIENT_SECRET")
BASE_URL = f"https://app.fakturoid.cz/api/v3/accounts/{SLUG}"
TOKEN_URL = "https://app.fakturoid.cz/api/v3/oauth/token"
USER_AGENT = "MotivusWebhook (synek.cz@gmail.com)"

# Token cache
_token_cache = {"access_token": None, "expires_at": 0}


def _get_access_token():
    """Get OAuth2 access token using Client Credentials flow."""
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["access_token"]

    resp = requests.post(
        TOKEN_URL,
        json={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 7200)
    return _token_cache["access_token"]


def _headers():
    return {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }


# ──────────────────────── Contacts (Odběratelé) ────────────────────────


def find_contact_by_email(email: str):
    """Search for an existing contact by email."""
    resp = requests.get(
        f"{BASE_URL}/subjects/search.json",
        params={"query": email},
        headers=_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    subjects = resp.json()
    for s in subjects:
        if s.get("email", "").lower() == email.lower():
            return s
    return None


def create_contact(name: str, email: str, phone: str = None):
    """Create a new contact (odběratel) in Fakturoid."""
    payload = {
        "name": name,
        "email": email,
        "type": "customer",
    }
    if phone:
        payload["phone"] = phone
    resp = requests.post(
        f"{BASE_URL}/subjects.json",
        json=payload,
        headers=_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_or_create_contact(name: str, email: str, phone: str = None):
    """Find existing contact or create a new one."""
    contact = find_contact_by_email(email)
    if contact:
        return contact
    return create_contact(name, email, phone)


# ──────────────────────── Invoices (Faktury) ────────────────────────


def create_invoice(
    contact_id: int,
    service_name: str,
    total_price: float,
    deposit_paid: float = 0,
    note: str = None,
    provider_name: str = "Mgr. Jiří Synek",
    provider_ico: str = "24400505",
):
    """
    Create and issue an invoice in Fakturoid.
    
    Args:
        contact_id: Fakturoid subject (contact) ID
        service_name: Name of the service (e.g. "Transformační koučink")
        total_price: Full price of the service in CZK
        deposit_paid: Amount already paid as deposit via Stripe
        note: Optional note on the invoice
        provider_name: Name of the OSVČ who provided the service
        provider_ico: IČO of the provider
    """
    lines = [
        {
            "name": service_name,
            "quantity": 1,
            "unit_name": "ks",
            "unit_price": total_price,
            "vat_rate": 0,  # Neplátce DPH
        }
    ]
    
    # Add deposit deduction line if deposit was paid
    if deposit_paid > 0:
        lines.append({
            "name": f"Zaplacená záloha (Stripe)",
            "quantity": 1,
            "unit_name": "ks",
            "unit_price": -deposit_paid,
            "vat_rate": 0,
        })

    payload = {
        "subject_id": contact_id,
        "lines": lines,
        "note": note or f"Poskytovatel služby: {provider_name}, IČO: {provider_ico}",
        "currency": "CZK",
        "payment_method": "bank",
        "vat_price_mode": "without_vat",  # Neplátce DPH
    }

    resp = requests.post(
        f"{BASE_URL}/invoices.json",
        json=payload,
        headers=_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    invoice = resp.json()
    
    # Mark as issued (send to client via email)
    fire_invoice(invoice["id"])
    
    return invoice


def fire_invoice(invoice_id: int):
    """Mark invoice as issued and send PDF to client via email."""
    resp = requests.post(
        f"{BASE_URL}/invoices/{invoice_id}/fire.json",
        json={"event": "deliver", "paid_at": None},
        headers=_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json() if resp.content else None


# ──────────────────────── Health Check ────────────────────────


def test_connection():
    """Test API connection and return account info."""
    resp = requests.get(
        f"{BASE_URL}/account.json",
        headers=_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    account = resp.json()
    return {
        "status": "ok",
        "name": account.get("name"),
        "slug": SLUG,
        "plan": account.get("plan"),
        "plan_price": account.get("plan_price"),
    }


if __name__ == "__main__":
    # Quick test
    print("Testing Fakturoid connection...")
    try:
        info = test_connection()
        print(f"[OK] Connected: {info['name']} (plan: {info['plan']})")
    except Exception as e:
        print(f"[ERROR] {e}")
