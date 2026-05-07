from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
RESULTS_DIR = ROOT_DIR / "results" / "raw"
SUMMARY_CSV_PATH = ROOT_DIR / "results" / "summary.csv"

STANDARD_SCENARIO = [
    (
        "Chcę wystawić fakturę. Sprzedawca to Aperture Solutions sp. z o.o., "
        "NIP 5271234567, ul. Marszałkowska 10/4, 00-001 Warszawa. "
        "Faktura dla Jana Kowalskiego, NIP 8431234560, ul. Długa 3/4, 30-200 Kraków. "
        "Dwie pozycje: konsultacje IT — 40 godzin po 150 zł netto, VAT 23%, "
        "oraz licencja oprogramowania — 1 sztuka, 2500 zł netto, VAT 23%. "
        "Płatność przelewem na konto 12 3456 7890 1234 5678 9012 3456, termin 14 dni."
    ),
    "Prawidłowy numer NIP sprzedawcy to 5260308476, a nabywcy 3623981230.",
    "Data wystawienia faktury to 2025-04-28 a sprzedaży to 2025-04-25, termin 14 dni.",
    "Tak, wszystko się zgadza. Proszę wygenerować fakturę w formacie JSON.",
]
