from src.application.tools.calculators import calculate_line, calculate_totals

def format_invoice(data: dict) -> dict:
    """Formatuje i zwraca gotowy JSON faktury VAT w restrykcyjnej strukturze.

    Oczekiwane parametry (przykłady):
    data: {
      "invoice": { "issue_date": "...", "sale_date": "...", "payment_due_date": "...", "payment_method": "...", "bank_account": "..." },
      "seller": { "name": "...", "nip": "...", "address": { "street": "...", "postal_code": "...", "city": "..." } },
      "buyer": { "name": "...", "nip": "...", "address": { "street": "...", "postal_code": "...", "city": "..." } },
      "line_items": [ { "name": "...", "quantity": 1, "unit": "...", "unit_price_net": 100.0, "vat_rate": "23%" } ]
    }

    Returns:
        Sformatowany słownik faktury ze wszystkimi wymaganymi polami, włącznie z adresami i kwotami (totals).
    """
    
    required_keys = {"invoice", "seller", "buyer", "line_items"}
    if missing := required_keys - set(data.keys()):
        return {"error": f"Brakujące sekcje w danych wejściowych: {missing}"}

    lines_calculated = []
    for item in data["line_items"]:
        quantity = item.get("quantity", item.get("qty", 0))
        unit_price_net = item.get("unit_price_net", item.get("net_price", item.get("price", 0.0)))
        calc = calculate_line(quantity, unit_price_net, item.get("vat_rate", "23%"))
        if "error" in calc:
            return {"error": f"Błąd w obliczeniach pozycji '{item.get('name')}': {calc['error']}"}
        lines_calculated.append({**item, **calc})

    totals = calculate_totals(lines_calculated)

    invoice = {
        "invoice": {
            "issue_date": data["invoice"].get("issue_date", ""),
            "sale_date": data["invoice"].get("sale_date", ""),
            "payment_due_date": data["invoice"].get("payment_due_date", ""),
            "payment_method": data["invoice"].get("payment_method", ""),
            "bank_account": data["invoice"].get("bank_account", "")
        },
        "seller": {
            "name": data["seller"].get("name", ""),
            "nip": data["seller"].get("nip", ""),
            "address": data["seller"].get("address", {})
        },
        "buyer": {
            "name": data["buyer"].get("name", ""),
            "nip": data["buyer"].get("nip", ""),
            "address": data["buyer"].get("address", {})
        },
        "line_items": lines_calculated,
        "totals": totals
    }
    return invoice