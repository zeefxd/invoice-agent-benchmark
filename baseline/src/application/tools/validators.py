import re

def validate_nip(nip: str) -> dict:
    """Sprawdza poprawność numeru NIP (polska suma kontrolna).

    Args:
        nip: Numer NIP jako string (może zawierać myślniki/spacje).

    Returns:
        Słownik z polem 'valid' (bool) i 'message' (str).
    """
    digits = re.sub(r"\D", "", nip)
    if len(digits) != 10: return {"valid": False, "message": f"NIP musi mieć 10 cyfr, podano {len(digits)}."}
    weights =[6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(int(digits[i]) * weights[i] for i in range(9)) % 11
    if checksum == int(digits[9]): return {"valid": True, "message": "NIP jest poprawny."}
    return {"valid": False, "message": "NIP ma błędną sumę kontrolną."}