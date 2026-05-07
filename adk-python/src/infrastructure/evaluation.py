import json


VAT_RATES = {"23%": 0.23, "8%": 0.08, "5%": 0.05, "0%": 0.0, "zw.": 0.0}


def extract_invoice_json(text: str) -> dict | None:
    candidates = []
    pos = 0
    while True:
        start = text.find("{", pos)
        if start == -1:
            break
        depth = 0
        for i, ch in enumerate(text[start:]):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    chunk = text[start : start + i + 1]
                    try:
                        candidates.append(json.loads(chunk))
                    except json.JSONDecodeError:
                        pass
                    pos = start + i + 1
                    break
        else:
            break

    for obj in reversed(candidates):
        if isinstance(obj, dict) and "invoice" in obj and "totals" in obj:
            return obj
    return None


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _safe_rate(vat_rate: str) -> float | None:
    if not isinstance(vat_rate, str):
        return None
    normalized = vat_rate.lower().replace(" ", "")
    return VAT_RATES.get(normalized)


def _validate_invoice_structure(invoice: dict | None) -> bool:
    if not isinstance(invoice, dict):
        return False

    required_root = {"invoice", "seller", "buyer", "line_items", "totals"}
    if not required_root.issubset(set(invoice.keys())):
        return False

    seller = invoice.get("seller", {})
    buyer = invoice.get("buyer", {})
    line_items = invoice.get("line_items", [])
    totals = invoice.get("totals", {})

    if not isinstance(seller, dict) or not isinstance(buyer, dict):
        return False
    if not isinstance(line_items, list) or len(line_items) < 1:
        return False
    if not isinstance(totals, dict):
        return False

    for party in (seller, buyer):
        if not _is_non_empty_string(party.get("name")):
            return False
        if not _is_non_empty_string(party.get("nip")):
            return False
        address = party.get("address")
        if not isinstance(address, dict):
            return False
        if not (_is_non_empty_string(address.get("street")) and _is_non_empty_string(address.get("postal_code")) and _is_non_empty_string(address.get("city"))):
            return False

    for item in line_items:
        if not isinstance(item, dict):
            return False
        required_line_keys = {
            "name",
            "quantity",
            "unit",
            "unit_price_net",
            "vat_rate",
            "net_total",
            "vat_amount",
            "gross_total",
        }
        if not required_line_keys.issubset(set(item.keys())):
            return False

    return True


def _validate_calculations(invoice: dict | None) -> bool:
    if not isinstance(invoice, dict):
        return False

    line_items = invoice.get("line_items", [])
    totals = invoice.get("totals", {})
    if not isinstance(line_items, list) or not isinstance(totals, dict):
        return False

    sum_net = 0.0
    sum_vat = 0.0
    sum_gross = 0.0

    for item in line_items:
        try:
            qty = float(item.get("quantity", 0))
            unit_price = float(item.get("unit_price_net", 0))
            net_total = float(item.get("net_total", 0))
            vat_amount = float(item.get("vat_amount", 0))
            gross_total = float(item.get("gross_total", 0))
        except (TypeError, ValueError):
            return False

        rate = _safe_rate(item.get("vat_rate", ""))
        if rate is None:
            return False

        expected_net = round(qty * unit_price, 2)
        expected_vat = round(expected_net * rate, 2)
        expected_gross = round(expected_net + expected_vat, 2)

        if round(net_total, 2) != expected_net:
            return False
        if round(vat_amount, 2) != expected_vat:
            return False
        if round(gross_total, 2) != expected_gross:
            return False

        sum_net += net_total
        sum_vat += vat_amount
        sum_gross += gross_total

    try:
        t_net = float(totals.get("net", 0))
        t_vat = float(totals.get("vat", 0))
        t_gross = float(totals.get("gross", 0))
    except (TypeError, ValueError):
        return False

    return (
        round(sum_net, 2) == round(t_net, 2)
        and round(sum_vat, 2) == round(t_vat, 2)
        and round(sum_gross, 2) == round(t_gross, 2)
    )


def _nip_validation_used(conversation_log: list[dict]) -> bool:
    for turn in conversation_log:
        if turn.get("role") != "agent":
            continue
        meta = turn.get("meta", {}) or {}
        tool_calls = meta.get("tool_calls", [])
        if isinstance(tool_calls, list) and "validate_nip" in tool_calls:
            return True
    return False


def evaluate_quality(conversation_log: list[dict]) -> dict:
    invoice_obj = None
    for turn in reversed(conversation_log):
        if turn.get("role") != "agent":
            continue
        content = turn.get("content", "")
        invoice_obj = extract_invoice_json(content)
        if invoice_obj:
            break

    checks = {
        "seller_data_correct": _validate_invoice_structure(invoice_obj),
        "buyer_data_correct": _validate_invoice_structure(invoice_obj),
        "nip_validation_triggered": _nip_validation_used(conversation_log),
        "calculations_correct": _validate_calculations(invoice_obj),
        "invoice_json_returned": _validate_invoice_structure(invoice_obj),
    }

    score = (sum(1 for ok in checks.values() if ok) / len(checks)) * 5
    return {"checks": checks, "auto_score_0_5": round(score, 2)}