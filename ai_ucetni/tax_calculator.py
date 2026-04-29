"""
Motivus AI Účetní — Czech Tax Calculator 2026
Continuous comparison: Paušální výdaje vs. Skutečné výdaje
"""

# ──────────────── 2026 Czech Tax Constants ────────────────

# Výdajové paušály (procento z příjmů)
EXPENSE_RATES = {
    "remeslna":   {"rate": 0.80, "limit": 1_600_000, "label": "Řemeslná živnost (80 %)"},
    "volna":      {"rate": 0.60, "limit": 1_200_000, "label": "Volná živnost (60 %)"},
    "svobodna":   {"rate": 0.40, "limit":   800_000, "label": "Svobodné povolání (40 %)"},
    "pronajem":   {"rate": 0.30, "limit":   600_000, "label": "Pronájem (30 %)"},
}

# Daň z příjmu
TAX_RATE_BASE = 0.15           # 15 % do limitu
TAX_RATE_HIGHER = 0.23         # 23 % nad limit (cca 1.9M Kč)
TAX_HIGHER_THRESHOLD = 36 * 48_967  # 36-násobek průměrné mzdy
TAX_CREDIT_TAXPAYER = 30_840   # Sleva na poplatníka 2026

# Sociální pojištění
SOCIAL_BASE_PERCENT = 0.55     # Vyměřovací základ = 55 % zisku
SOCIAL_RATE = 0.292            # 29.2 %
SOCIAL_MIN_MONTHLY = 5_720     # Min. záloha hlavní činnost
SOCIAL_MIN_MONTHLY_SIDE = 1_574  # Min. záloha vedlejší činnost

# Zdravotní pojištění
HEALTH_BASE_PERCENT = 0.50     # Vyměřovací základ = 50 % zisku
HEALTH_RATE = 0.135            # 13.5 %
HEALTH_MIN_MONTHLY = 3_306     # Min. záloha

# DPH
VAT_TURNOVER_LIMIT = 2_000_000  # Registrační limit obratu za 12 měsíců

# Průměrná mzda 2026
AVERAGE_WAGE_2026 = 48_967


def calculate_income_tax(profit: float) -> float:
    """Calculate income tax with progressive rates and taxpayer credit."""
    if profit <= 0:
        return 0.0
    
    if profit <= TAX_HIGHER_THRESHOLD:
        tax = profit * TAX_RATE_BASE
    else:
        tax = (TAX_HIGHER_THRESHOLD * TAX_RATE_BASE +
               (profit - TAX_HIGHER_THRESHOLD) * TAX_RATE_HIGHER)
    
    # Apply taxpayer credit
    tax = max(0, tax - TAX_CREDIT_TAXPAYER)
    return round(tax, 2)


# Rozhodná částka pro vedlejší činnost 2026
SOCIAL_SIDE_THRESHOLD = 105_520  # Pod touto hranicí zisku neplatíte SP


def calculate_social_insurance(profit: float, is_main: bool = True) -> float:
    """Calculate annual social insurance."""
    # Vedlejší činnost: pod rozhodnou částkou se SP neplatí vůbec
    if not is_main and profit <= SOCIAL_SIDE_THRESHOLD:
        return 0.0
    
    if profit <= 0:
        if is_main:
            return SOCIAL_MIN_MONTHLY * 12
        return 0.0
    
    base = profit * SOCIAL_BASE_PERCENT
    insurance = base * SOCIAL_RATE
    min_annual = (SOCIAL_MIN_MONTHLY if is_main else SOCIAL_MIN_MONTHLY_SIDE) * 12
    
    return round(max(insurance, min_annual), 2)


def calculate_health_insurance(profit: float, is_main: bool = True) -> float:
    """Calculate annual health insurance."""
    # Vedlejší činnost: ZP platí zaměstnavatel, OSVČ neplatí nic
    if not is_main:
        return 0.0
    
    if profit <= 0:
        return HEALTH_MIN_MONTHLY * 12
    
    base = profit * HEALTH_BASE_PERCENT
    insurance = base * HEALTH_RATE
    min_annual = HEALTH_MIN_MONTHLY * 12
    
    return round(max(insurance, min_annual), 2)


def compare_strategies(
    income_ytd: float,
    expenses_ytd: float,
    activity_type: str = "volna",
    is_main_activity: bool = False,
) -> dict:
    """
    Compare flat-rate (paušál) vs. actual expenses strategy.
    
    Returns comprehensive comparison with recommendation.
    """
    rate_info = EXPENSE_RATES.get(activity_type, EXPENSE_RATES["volna"])
    rate = rate_info["rate"]
    limit = rate_info["limit"]
    
    # ── Scénář A: Výdajový paušál ──
    pausal_expenses = min(income_ytd * rate, limit)
    profit_pausal = max(0, income_ytd - pausal_expenses)
    
    tax_pausal = calculate_income_tax(profit_pausal)
    social_pausal = calculate_social_insurance(profit_pausal, is_main_activity)
    health_pausal = calculate_health_insurance(profit_pausal, is_main_activity)
    total_levies_pausal = tax_pausal + social_pausal + health_pausal
    net_pausal = income_ytd - pausal_expenses - total_levies_pausal
    
    # ── Scénář B: Skutečné výdaje ──
    profit_actual = max(0, income_ytd - expenses_ytd)
    
    tax_actual = calculate_income_tax(profit_actual)
    social_actual = calculate_social_insurance(profit_actual, is_main_activity)
    health_actual = calculate_health_insurance(profit_actual, is_main_activity)
    total_levies_actual = tax_actual + social_actual + health_actual
    net_actual = income_ytd - expenses_ytd - total_levies_actual
    
    # ── Doporučení ──
    if net_pausal >= net_actual:
        recommended = "pausal"
        advantage = net_pausal - net_actual
    else:
        recommended = "actual"
        advantage = net_actual - net_pausal
    
    # ── DPH varování ──
    vat_warning = None
    vat_remaining = VAT_TURNOVER_LIMIT - income_ytd
    if vat_remaining <= 200_000 and vat_remaining > 0:
        vat_warning = f"POZOR: Do registrace platce DPH zbyva {vat_remaining:,.0f} Kc!"
    elif vat_remaining <= 0:
        vat_warning = "PREKROCEN LIMIT! Povinnost registrace platce DPH."
    
    return {
        "income_ytd": income_ytd,
        "expenses_ytd": expenses_ytd,
        "activity_type": rate_info["label"],
        "recommended": recommended,
        "advantage": round(advantage, 2),
        "pausal": {
            "expenses": round(pausal_expenses, 2),
            "profit": round(profit_pausal, 2),
            "tax": round(tax_pausal, 2),
            "social": round(social_pausal, 2),
            "health": round(health_pausal, 2),
            "total_levies": round(total_levies_pausal, 2),
            "net_income": round(net_pausal, 2),
        },
        "actual": {
            "expenses": round(expenses_ytd, 2),
            "profit": round(profit_actual, 2),
            "tax": round(tax_actual, 2),
            "social": round(social_actual, 2),
            "health": round(health_actual, 2),
            "total_levies": round(total_levies_actual, 2),
            "net_income": round(net_actual, 2),
        },
        "monthly_reserves": {
            "social": SOCIAL_MIN_MONTHLY if is_main_activity else SOCIAL_MIN_MONTHLY_SIDE,
            "health": HEALTH_MIN_MONTHLY,
            "total": (SOCIAL_MIN_MONTHLY if is_main_activity else SOCIAL_MIN_MONTHLY_SIDE) + HEALTH_MIN_MONTHLY,
        },
        "vat_warning": vat_warning,
        "vat_remaining": max(0, vat_remaining),
    }


def format_comparison(result: dict) -> str:
    """Format comparison result as a readable text report."""
    r = result
    p = r["pausal"]
    a = r["actual"]
    
    lines = [
        "=" * 50,
        "  MOTIVUS AI UCETNI -- POROVNANI STRATEGII",
        "=" * 50,
        "",
        f"  Prijmy (od zacatku roku):  {r['income_ytd']:>12,.0f} Kc",
        f"  Skutecne vydaje:           {r['expenses_ytd']:>12,.0f} Kc",
        f"  Typ cinnosti:              {r['activity_type']}",
        "",
        "-" * 50,
        "  SCENAR A: PAUSALNI VYDAJE",
        "-" * 50,
        f"  Pausalni vydaje:           {p['expenses']:>12,.0f} Kc",
        f"  Zaklad dane (zisk):        {p['profit']:>12,.0f} Kc",
        f"  Dan z prijmu:              {p['tax']:>12,.0f} Kc",
        f"  Socialni pojisteni:        {p['social']:>12,.0f} Kc",
        f"  Zdravotni pojisteni:       {p['health']:>12,.0f} Kc",
        f"  CISTY PRIJEM:              {p['net_income']:>12,.0f} Kc",
        "",
        "-" * 50,
        "  SCENAR B: SKUTECNE VYDAJE",
        "-" * 50,
        f"  Skutecne vydaje:           {a['expenses']:>12,.0f} Kc",
        f"  Zaklad dane (zisk):        {a['profit']:>12,.0f} Kc",
        f"  Dan z prijmu:              {a['tax']:>12,.0f} Kc",
        f"  Socialni pojisteni:        {a['social']:>12,.0f} Kc",
        f"  Zdravotni pojisteni:       {a['health']:>12,.0f} Kc",
        f"  CISTY PRIJEM:              {a['net_income']:>12,.0f} Kc",
        "",
        "=" * 50,
    ]
    
    rec_label = "PAUSALNI VYDAJE" if r["recommended"] == "pausal" else "SKUTECNE VYDAJE"
    lines.append(f"  >> DOPORUCENI: {rec_label}")
    lines.append(f"     Vyhoda oproti alternativve: {r['advantage']:,.0f} Kc")
    
    if r["vat_warning"]:
        lines.append("")
        lines.append(f"  !! {r['vat_warning']}")
    
    lines.append("")
    lines.append(f"  Mesicni zalohy: SP {r['monthly_reserves']['social']:,} Kc"
                 f" + ZP {r['monthly_reserves']['health']:,} Kc"
                 f" = {r['monthly_reserves']['total']:,} Kc")
    lines.append("=" * 50)
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test: Jiří má příjem 140 000 Kč a výdaje 47 200 Kč
    print("\n--- Test: Jiri, volna zivnost ---")
    result = compare_strategies(
        income_ytd=140_000,
        expenses_ytd=47_200,
        activity_type="volna",
    )
    print(format_comparison(result))
    
    # Test: Vysoký příjem blízko DPH limitu
    print("\n--- Test: Vysoke prijmy (blizko DPH) ---")
    result2 = compare_strategies(
        income_ytd=1_850_000,
        expenses_ytd=420_000,
        activity_type="volna",
    )
    print(format_comparison(result2))
