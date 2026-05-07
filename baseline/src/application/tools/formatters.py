from src.application.tools.calculators import calculate_line, calculate_totals

REQUIRED_INVOICE_FIELDS = (
    "issue_date",
    "sale_date",
    "payment_due_date",
    "payment_method",
    "bank_account",
)

REQUIRED_PARTY_FIELDS = ("name", "nip", "address")
REQUIRED_ADDRESS_FIELDS = ("street", "postal_code", "city")
REQUIRED_LINE_FIELDS = ("name", "quantity", "unit", "unit_price_net", "vat_rate")


def _pick_value(source: dict, *keys: str) -> str:
    for key in keys:
        value = source.get(key)
        if value not in (None, ""):
            return value
    return ""


def _normalize_address(address: dict | str) -> dict:
    if isinstance(address, dict):
        return {
            "street": address.get("street", ""),
            "postal_code": address.get("postal_code", ""),
            "city": address.get("city", ""),
        }

    if isinstance(address, str):
        return {"street": address, "postal_code": "", "city": ""}

    return {"street": "", "postal_code": "", "city": ""}


def _validate_required_fields(section_name: str, payload: dict, required_fields: tuple[str, ...]) -> list[str]:
    missing = []
    for field in required_fields:
        if field not in payload or payload.get(field) in (None, "", {}):
            missing.append(f"{section_name}.{field}")
    return missing


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
    
    if not data or not isinstance(data, dict):
        return {"error": "Dane wejściowe muszą być obiektem JSON."}

    required_keys = {"invoice", "seller", "buyer", "line_items"}
    if missing := required_keys - set(data.keys()):
        return {"error": f"Brakujące sekcje w danych wejściowych: {sorted(missing)}"}

    invoice_section = data.get("invoice", {})
    seller_section = data.get("seller", {})
    buyer_section = data.get("buyer", {})

    missing_fields = []
    if not isinstance(invoice_section, dict):
        return {"error": "Sekcja invoice musi być obiektem JSON."}
    if not isinstance(seller_section, dict):
        return {"error": "Sekcja seller musi być obiektem JSON."}
    if not isinstance(buyer_section, dict):
        return {"error": "Sekcja buyer musi być obiektem JSON."}

    missing_fields.extend(_validate_required_fields("invoice", invoice_section, REQUIRED_INVOICE_FIELDS))
    missing_fields.extend(_validate_required_fields("seller", seller_section, REQUIRED_PARTY_FIELDS))
    missing_fields.extend(_validate_required_fields("buyer", buyer_section, REQUIRED_PARTY_FIELDS))

    seller_address = _normalize_address(seller_section.get("address", {}))
    buyer_address = _normalize_address(buyer_section.get("address", {}))
    missing_fields.extend(_validate_required_fields("seller.address", seller_address, REQUIRED_ADDRESS_FIELDS))
    missing_fields.extend(_validate_required_fields("buyer.address", buyer_address, REQUIRED_ADDRESS_FIELDS))

    if missing_fields:
        return {"error": f"Brakujące wymagane pola: {missing_fields}"}

    lines_calculated = []
    if not isinstance(data["line_items"], list) or len(data["line_items"]) == 0:
        return {"error": "line_items musi być niepustą listą."}

    for index, item in enumerate(data["line_items"], start=1):
        if not isinstance(item, dict):
            return {"error": f"Pozycja {index} musi być obiektem JSON."}

        missing_line = [field for field in REQUIRED_LINE_FIELDS if field not in item or item.get(field) in (None, "")]
        if missing_line:
            return {"error": f"Brakujące pola w pozycji {index}: {missing_line}"}

        quantity = item.get("quantity", item.get("qty", 0))
        unit_price_net = item.get("unit_price_net", item.get("net_price", item.get("price", 0.0)))
        calc = calculate_line(quantity, unit_price_net, item.get("vat_rate", "23%"))
        if "error" in calc:
            return {"error": f"Błąd w obliczeniach pozycji '{item.get('name')}': {calc['error']}"}
        lines_calculated.append({**item, **calc})

    totals = calculate_totals(lines_calculated)

    invoice = {
        "invoice": {
            "issue_date": _pick_value(invoice_section, "issue_date", "invoice_date"),
            "sale_date": _pick_value(invoice_section, "sale_date", "sales_date"),
            "payment_due_date": _pick_value(invoice_section, "payment_due_date", "due_date"),
            "payment_method": _pick_value(invoice_section, "payment_method", "paymentMethod"),
            "bank_account": _pick_value(invoice_section, "bank_account", "bankAccount")
        },
        "seller": {
            "name": seller_section.get("name", ""),
            "nip": seller_section.get("nip", ""),
            "address": seller_address
        },
        "buyer": {
            "name": buyer_section.get("name", ""),
            "nip": buyer_section.get("nip", ""),
            "address": buyer_address
        },
        "line_items": lines_calculated,
        "totals": totals
    }
    return invoice