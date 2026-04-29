import json
import re
import os

from datetime import date, timedelta
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

def validate_nip(nip: str) -> dict:
    """Sprawdza poprawność numeru NIP (polska suma kontrolna).

    Args:
        nip: Numer NIP jako string (może zawierać myślniki/spacje).

    Returns:
        Słownik z polem 'valid' (bool) i 'message' (str).
    """
    digits = re.sub(r"\D", "", nip)
    if len(digits) != 10:
        return {"valid": False, "message": f"NIP musi mieć 10 cyfr, podano {len(digits)}."}
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(int(digits[i]) * weights[i] for i in range(9)) % 11
    if checksum == int(digits[9]):
        return {"valid": True, "message": "NIP jest poprawny."}
    return {"valid": False, "message": "NIP ma błędną sumę kontrolną."}

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
        calc = calculate_line(item.get("quantity", 0), item.get("unit_price_net", 0.0), item.get("vat_rate", "23%"))
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

SYSTEM_PROMPT = """Jesteś profesjonalnym, rzetelnym asystentem do wystawiania faktur VAT w Polsce.
Prowadzisz konwersację z użytkownikiem w celu zebrania danych do faktury.

KATEGORYCZNIE ZABRONIONE JEST UŻYWANIE JAKICHKOLWIEK EMOTIKONÓW (EMOJI) W CAŁEJ ROZMOWIE.

DANE DO ZEBRANIA:
1. Sprzedawca: nazwa firmy, NIP (waliduj!), adres (ulica, kod, miasto)
2. Nabywca: nazwa/imię i nazwisko, NIP (jeśli firma, waliduj!), adres
3. Pozycje (min. 1): nazwa, ilość, jednostka, cena netto, stawka VAT (23%/8%/5%/0%/zw.)
4. Faktura: data wystawienia, data sprzedaży, termin płatności, metoda płatności, konto bankowe (jeśli przelew)

ZASADY:
- Nie używaj emotikonów pod żadnym pozorem!
- Pytaj o brakujące dane naturalnie, nie wymuszaj kolejności. Zamieniaj się z użytkownikiem rundami w dialogu.
- Zawsze waliduj NIP za pomocą narzędzia validate_nip.
- Dla każdej pozycji użyj calculate_line do obliczenia wartości.
- Po zebraniu wszystkich danych: podsumuj fakturę i poproś o potwierdzenie.
- Po potwierdzeniu: użyj narzędzia format_invoice. PRZEKAŻ MU bezwzględnie obiekt JSON mający w głównym węźle TYLKO klucze: "invoice", "seller", "buyer", "line_items" (NIGDY nie wstawiaj ich wewnątrz dodatkowego obiektu typu "data"!).
- Jeśli użytkownik podał datę sprzedaży i termin płatności jako "14 dni", oblicz datę jako data_sprzedaży + 14 dni.
- Domyślna data wystawienia to dzisiaj, chyba że użytkownik poda inną.

WAŻNE ZASADY FUNKCJI I NARZĘDZI (TOOL CALLING):
- Masz do dyspozycji TYLKO narzędzia: validate_nip, calculate_line, calculate_totals, format_invoice.
- NIGDY NIE ZMYŚLAJ innych narzędzi (np. "assistant", "reply", "ask_user"). 
- Jeśli zadajesz pytanie użytkownikowi lub odpowiadasz bezpośrednio jemu, ODPOWIEDZ ZWYKŁYM TEKSTEM (zwróć string konwersacji), a nie poprzez tworzenie JSONa jak przy wywoływaniu funkcji!
- Wywołuj funkcje (formatując jako call tool JSON) tylko wtedy, gdy musisz przeliczyć coś matematycznie albo zwalidować.
- Twoja FINALNA ODPOWIEDŹ po uruchomieniu narzędzia format_invoice to MA BYĆ WYŁĄCZNIE CZYSTY JSON, dokładnie w takiej postaci, jaką przed chwilą zwróciło narzędzie. Żadnego dodatkowego tekstu ani formatowania.
"""

root_agent = Agent(
    name="invoice_agent",
    model=LiteLlm(model="ollama_chat/gemma-4"),
    description="Agent do wypełniania faktur VAT",
    instruction=SYSTEM_PROMPT,
    tools=[validate_nip, calculate_line, calculate_totals, format_invoice],
)