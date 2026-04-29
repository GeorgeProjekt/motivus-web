"""
Motivus AI Účetní — Main CLI Interface
Connects all components: OCR, Database, Tax Calculator.

Usage:
    python ai_ucetni/main.py init                     # Initialize DB + seed providers
    python ai_ucetni/main.py scan <image_path>        # Scan a receipt
    python ai_ucetni/main.py add-income <amount>      # Add income manually
    python ai_ucetni/main.py status                   # Show current tax status
    python ai_ucetni/main.py report                   # Generate detailed report
    python ai_ucetni/main.py expenses                 # List recent expenses
"""
import sys
import os

# Ensure the ai_ucetni package is importable
sys.path.insert(0, os.path.dirname(__file__))

from database import (
    init_db, add_provider, get_all_providers, get_provider,
    add_income, get_income_ytd, get_income_month,
    add_expense, get_expenses_ytd, get_expenses_by_category, get_recent_expenses,
)
from tax_calculator import compare_strategies, format_comparison
from datetime import datetime


def cmd_init():
    """Initialize database and seed Motivus providers."""
    init_db()
    
    providers = get_all_providers()
    if not providers:
        print("\nSeeding providers...")
        add_provider(
            name="Mgr. Jiri Synek",
            ico="24400505",
            expense_rate=60,
            email="synek.cz@gmail.com",
            activity_type="volna",
        )
        print("  [+] Jiri Synek (ICO 24400505, 60 %)")
        
        # Uncomment when IČO is known:
        # add_provider(name="Kristyna Nosova", ico="XXXXXXXX", expense_rate=60, activity_type="volna")
        # add_provider(name="Michal Smolik", ico="XXXXXXXX", expense_rate=60, activity_type="volna")
        
        print("\n[OK] Providers seeded. Add more with database.add_provider()")
    else:
        print(f"\n[OK] Database already has {len(providers)} provider(s):")
        for p in providers:
            print(f"  [{p['id']}] {p['name']} (ICO {p['ico']}, {p['expense_rate']} %)")


def cmd_scan(image_path: str, provider_id: int = 1):
    """Scan a receipt image and add to database."""
    try:
        from ocr_pipeline import extract_receipt, format_receipt
    except ImportError:
        print("[ERROR] OpenAI not configured. Set OPENAI_API_KEY in .env")
        return
    
    if not os.path.exists(image_path):
        print(f"[ERROR] File not found: {image_path}")
        return
    
    provider = get_provider(provider_id)
    if not provider:
        print(f"[ERROR] Provider #{provider_id} not found. Run 'init' first.")
        return
    
    print(f"Scanning receipt for {provider['name']}...")
    print(f"Image: {image_path}")
    print("-" * 40)
    
    receipt = extract_receipt(image_path)
    print(format_receipt(receipt))
    print("-" * 40)
    
    # Save to database
    eid = add_expense(
        provider_id=provider_id,
        vendor_name=receipt.vendor_name,
        vendor_ico=receipt.vendor_ico,
        amount=receipt.total_amount,
        vat_amount=receipt.vat_amount or 0,
        category=receipt.category,
        description=receipt.description,
        date_str=receipt.date,
        payment_method=receipt.payment_method,
        is_deductible=receipt.is_deductible,
        receipt_image_path=os.path.abspath(image_path),
        confidence=receipt.confidence,
        raw_ocr_text=receipt.raw_text,
    )
    print(f"[OK] Saved as expense #{eid}")
    
    # Show updated status
    print("\n")
    cmd_status(provider_id)


def cmd_add_income(amount: float, provider_id: int = 1,
                   source: str = "cash", service: str = None, client: str = None):
    """Add income entry manually."""
    provider = get_provider(provider_id)
    if not provider:
        print(f"[ERROR] Provider #{provider_id} not found.")
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    iid = add_income(
        provider_id=provider_id,
        amount=amount,
        date_str=today,
        source=source,
        service_name=service,
        client_name=client,
    )
    print(f"[OK] Income #{iid}: {amount:,.0f} Kc added for {provider['name']}")
    print()
    cmd_status(provider_id)


def cmd_status(provider_id: int = 1):
    """Show current tax status and recommendation."""
    provider = get_provider(provider_id)
    if not provider:
        print(f"[ERROR] Provider #{provider_id} not found.")
        return
    
    year = datetime.now().year
    income_ytd = get_income_ytd(provider_id, year)
    expenses_ytd = get_expenses_ytd(provider_id, year)
    
    result = compare_strategies(
        income_ytd=income_ytd,
        expenses_ytd=expenses_ytd,
        activity_type=provider.get("activity_type", "volna"),
    )
    
    print(f"\n  Provider: {provider['name']} (ICO {provider['ico']})")
    print(format_comparison(result))


def cmd_report(provider_id: int = 1):
    """Generate detailed report with expense breakdown."""
    provider = get_provider(provider_id)
    if not provider:
        print(f"[ERROR] Provider #{provider_id} not found.")
        return
    
    year = datetime.now().year
    month = datetime.now().month
    income_ytd = get_income_ytd(provider_id, year)
    income_month = get_income_month(provider_id, year, month)
    expenses_ytd = get_expenses_ytd(provider_id, year)
    categories = get_expenses_by_category(provider_id, year)
    
    result = compare_strategies(
        income_ytd=income_ytd,
        expenses_ytd=expenses_ytd,
        activity_type=provider.get("activity_type", "volna"),
    )
    
    print(f"\n{'=' * 55}")
    print(f"  MOTIVUS AI UCETNI -- MESICNI REPORT")
    print(f"  {provider['name']} | {datetime.now().strftime('%B %Y')}")
    print(f"{'=' * 55}")
    
    print(f"\n  Prijmy tento mesic:     {income_month:>12,.0f} Kc")
    print(f"  Prijmy od zacatku roku: {income_ytd:>12,.0f} Kc")
    print(f"  Vydaje od zacatku roku: {expenses_ytd:>12,.0f} Kc")
    
    if categories:
        print(f"\n  {'KATEGORIE':<20} {'POCET':>6} {'CASTKA':>12}")
        print(f"  {'-'*20} {'-'*6} {'-'*12}")
        for cat in categories:
            print(f"  {cat['category']:<20} {cat['count']:>6} {cat['total']:>11,.0f} Kc")
    
    print(format_comparison(result))


def cmd_expenses(provider_id: int = 1, limit: int = 10):
    """List recent expenses."""
    expenses = get_recent_expenses(provider_id, limit)
    if not expenses:
        print("[INFO] No expenses recorded yet.")
        return
    
    print(f"\n  {'DATUM':<12} {'DODAVATEL':<20} {'KATEGORIE':<15} {'CASTKA':>10}")
    print(f"  {'-'*12} {'-'*20} {'-'*15} {'-'*10}")
    for e in expenses:
        vendor = e['vendor_name'][:18]
        cat = e['category'][:13]
        deduct = "" if e['is_deductible'] else " *"
        print(f"  {e['date']:<12} {vendor:<20} {cat:<15} {e['amount']:>9,.0f} Kc{deduct}")
    
    print(f"\n  * = osobni vydaj (danove neuznatelny)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        cmd_init()
    
    elif command == "scan":
        if len(sys.argv) < 3:
            print("Usage: python main.py scan <image_path> [provider_id]")
            return
        pid = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        cmd_scan(sys.argv[2], pid)
    
    elif command == "add-income":
        if len(sys.argv) < 3:
            print("Usage: python main.py add-income <amount> [provider_id]")
            return
        pid = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        cmd_add_income(float(sys.argv[2]), pid)
    
    elif command == "status":
        pid = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        cmd_status(pid)
    
    elif command == "report":
        pid = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        cmd_report(pid)
    
    elif command == "expenses":
        pid = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        cmd_expenses(pid)
    
    else:
        print(f"[ERROR] Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
