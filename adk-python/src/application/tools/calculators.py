def calculate_line(quantity: float, unit_price_net: float, vat_rate: str) -> dict:
    """Oblicza wartości netto, VAT i brutto dla jednej pozycji faktury.

    Args:
        quantity: Ilość.
        unit_price_net: Cena netto za jednostkę.
        vat_rate: Stawka VAT jako string, np. "23%", "8%", "5%", "0%", "zw.".

    Returns:
        Słownik z polami net_total, vat_amount, gross_total.
    """
    
    RATES = {"23%": 0.23, "8%": 0.08, "5%": 0.05, "0%": 0.00, "zw.": 0.00}
    rate = RATES.get(vat_rate.lower().replace(" ", ""))
    if rate is None:
        return {"error": f"Nieznana stawka VAT: {vat_rate}. Dozwolone: {list(RATES.keys())}"}
    net_total = round(quantity * unit_price_net, 2)
    vat_amount = round(net_total * rate, 2)
    gross_total = round(net_total + vat_amount, 2)
    return {
        "net_total": net_total,
        "vat_amount": vat_amount,
        "gross_total": gross_total,
    }

def calculate_totals(lines: list) -> dict:
    """Oblicza sumy netto, VAT i brutto dla wszystkich pozycji faktury.

    Args:
        lines: Lista słowników z polami net_total, vat_amount, gross_total.

    Returns:
        Słownik z polami net, vat, gross.
    """
    
    net = round(sum(l.get("net_total", 0) for l in lines), 2)
    vat = round(sum(l.get("vat_amount", 0) for l in lines), 2)
    gross = round(sum(l.get("gross_total", 0) for l in lines), 2)
    return {"net": net, "vat": vat, "gross": gross}
