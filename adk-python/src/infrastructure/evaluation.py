import json

def extract_invoice_json(text: str) -> dict | None:
    candidates =[]
    pos = 0
    while True:
        start = text.find("{", pos)
        if start == -1: break
        depth = 0
        for i, ch in enumerate(text[start:]):
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try: candidates.append(json.loads(text[start: start + i + 1]))
                    except json.JSONDecodeError: pass
                    pos = start + i + 1
                    break
        else: break
    for obj in reversed(candidates):
        if "invoice" in obj and "totals" in obj: return obj
    return None

def evaluate_quality(conversation_log: list[dict]) -> dict:
    full_text = " ".join(t["content"] for t in conversation_log if t["role"] == "agent").lower()
    checks = {
        "seller_data_correct": "5260308476" in full_text and "aperture" in full_text,
        "buyer_data_correct": "3623981230" in full_text and "kowalski" in full_text,
        "nip_validation_triggered": any(word in full_text for word in["błędn", "niepoprawn", "poprawn", "zgodn", "sprawdzon"]),
        "calculations_correct": "8500" in full_text and "10455" in full_text,
        "invoice_json_returned": '"invoice"' in full_text and '"totals"' in full_text,
    }
    score = sum(1 for v in checks.values() if v) / len(checks) * 5
    return {"checks": checks, "auto_score_0_5": round(score, 2)}