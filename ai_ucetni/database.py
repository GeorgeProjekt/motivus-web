"""
Motivus AI Účetní — Database Models
SQLite database for tracking income, expenses, and tax optimization.
"""
import sqlite3
import os
from datetime import datetime, date
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "ucetni.db")


def get_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        -- Poskytovatelé (OSVČ v týmu)
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ico TEXT NOT NULL UNIQUE,
            expense_rate INTEGER DEFAULT 60,
            expense_rate_limit INTEGER DEFAULT 1200000,
            activity_type TEXT DEFAULT 'volna',
            whatsapp_number TEXT,
            email TEXT,
            is_vat_payer BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Příjmy (z Fakturoidu / Stripe / hotovosti)
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER NOT NULL REFERENCES providers(id),
            amount REAL NOT NULL,
            source TEXT DEFAULT 'cash',
            client_name TEXT,
            service_name TEXT,
            invoice_id TEXT,
            date DATE NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Výdaje (z OCR účtenek)
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER NOT NULL REFERENCES providers(id),
            vendor_name TEXT NOT NULL,
            vendor_ico TEXT,
            amount REAL NOT NULL,
            vat_amount REAL DEFAULT 0,
            category TEXT NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            payment_method TEXT DEFAULT 'card',
            is_deductible BOOLEAN DEFAULT 1,
            receipt_image_path TEXT,
            confidence REAL DEFAULT 1.0,
            raw_ocr_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Měsíční snapshoty
        CREATE TABLE IF NOT EXISTS monthly_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER NOT NULL REFERENCES providers(id),
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            total_income REAL DEFAULT 0,
            total_expenses_actual REAL DEFAULT 0,
            total_expenses_pausal REAL DEFAULT 0,
            recommended_strategy TEXT DEFAULT 'pausal',
            tax_estimate REAL DEFAULT 0,
            social_insurance_estimate REAL DEFAULT 0,
            health_insurance_estimate REAL DEFAULT 0,
            net_profit_estimate REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(provider_id, year, month)
        );

        -- Čekající sezení (Zaplacené zálohy)
        CREATE TABLE IF NOT EXISTS pending_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER NOT NULL REFERENCES providers(id),
            client_name TEXT,
            client_email TEXT,
            client_phone TEXT,
            service_name TEXT,
            service_key TEXT,
            total_price REAL NOT NULL,
            deposit_paid REAL NOT NULL,
            stripe_intent_id TEXT UNIQUE,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized: {DB_PATH}")


# ──────────────── Provider CRUD ────────────────


def add_provider(name: str, ico: str, expense_rate: int = 60,
                 email: str = None, whatsapp: str = None,
                 activity_type: str = "volna") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO providers (name, ico, expense_rate, email, whatsapp_number, activity_type)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, ico, expense_rate, email, whatsapp, activity_type)
    )
    conn.commit()
    pid = cursor.lastrowid
    conn.close()
    return pid


def get_provider(provider_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM providers WHERE id = ?", (provider_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_providers() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM providers ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────── Income CRUD ────────────────


def add_income(provider_id: int, amount: float, date_str: str,
               source: str = "cash", client_name: str = None,
               service_name: str = None, invoice_id: str = None,
               note: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO income (provider_id, amount, date, source, client_name,
           service_name, invoice_id, note)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (provider_id, amount, date_str, source, client_name,
         service_name, invoice_id, note)
    )
    conn.commit()
    iid = cursor.lastrowid
    conn.close()
    return iid


def get_income_ytd(provider_id: int, year: int = None) -> float:
    """Get total income year-to-date."""
    year = year or datetime.now().year
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM income WHERE provider_id = ? AND strftime('%Y', date) = ?",
        (provider_id, str(year))
    ).fetchone()
    conn.close()
    return row["total"]


def get_income_month(provider_id: int, year: int = None, month: int = None) -> float:
    year = year or datetime.now().year
    month = month or datetime.now().month
    conn = get_connection()
    row = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM income
           WHERE provider_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?""",
        (provider_id, str(year), f"{month:02d}")
    ).fetchone()
    conn.close()
    return row["total"]


# ──────────────── Expense CRUD ────────────────


def add_expense(provider_id: int, vendor_name: str, amount: float,
                date_str: str, category: str, description: str = None,
                vendor_ico: str = None, vat_amount: float = 0,
                payment_method: str = "card", is_deductible: bool = True,
                receipt_image_path: str = None, confidence: float = 1.0,
                raw_ocr_text: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO expenses (provider_id, vendor_name, vendor_ico, amount,
           vat_amount, category, description, date, payment_method, is_deductible,
           receipt_image_path, confidence, raw_ocr_text)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (provider_id, vendor_name, vendor_ico, amount, vat_amount,
         category, description, date_str, payment_method, is_deductible,
         receipt_image_path, confidence, raw_ocr_text)
    )
    conn.commit()
    eid = cursor.lastrowid
    conn.close()
    return eid


def get_expenses_ytd(provider_id: int, year: int = None, deductible_only: bool = True) -> float:
    """Get total deductible expenses year-to-date."""
    year = year or datetime.now().year
    conn = get_connection()
    query = "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE provider_id = ? AND strftime('%Y', date) = ?"
    params = [provider_id, str(year)]
    if deductible_only:
        query += " AND is_deductible = 1"
    row = conn.execute(query, params).fetchone()
    conn.close()
    return row["total"]


def get_expenses_by_category(provider_id: int, year: int = None) -> list:
    """Get expenses grouped by category."""
    year = year or datetime.now().year
    conn = get_connection()
    rows = conn.execute(
        """SELECT category, COUNT(*) as count, SUM(amount) as total
           FROM expenses WHERE provider_id = ? AND strftime('%Y', date) = ? AND is_deductible = 1
           GROUP BY category ORDER BY total DESC""",
        (provider_id, str(year))
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_expenses(provider_id: int, limit: int = 10) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE provider_id = ? ORDER BY date DESC LIMIT ?",
        (provider_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────── Pending Sessions CRUD ────────────────


def add_pending_session(provider_id: int, client_name: str, client_email: str,
                        service_name: str, total_price: float, deposit_paid: float,
                        stripe_intent_id: str, service_key: str = None, client_phone: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO pending_sessions (provider_id, client_name, client_email, client_phone,
           service_name, service_key, total_price, deposit_paid, stripe_intent_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (provider_id, client_name, client_email, client_phone,
         service_name, service_key, total_price, deposit_paid, stripe_intent_id)
    )
    conn.commit()
    sid = cursor.lastrowid
    conn.close()
    return sid


def get_pending_sessions(provider_id: int = None) -> list:
    conn = get_connection()
    if provider_id:
        rows = conn.execute("SELECT * FROM pending_sessions WHERE provider_id = ? AND status = 'pending' ORDER BY created_at DESC", (provider_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM pending_sessions WHERE status = 'pending' ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session(session_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM pending_sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def mark_session_invoiced(session_id: int):
    conn = get_connection()
    conn.execute("UPDATE pending_sessions SET status = 'invoiced' WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def mark_session_cancelled(session_id: int):
    conn = get_connection()
    conn.execute("UPDATE pending_sessions SET status = 'cancelled' WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("[OK] Database ready.")
