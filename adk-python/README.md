# ADK Python - Invoice Agent Benchmark

Implementacja agenta fakturowego VAT w Google ADK (Python).

## Zakres

- Konwersacja z uzytkownikiem i zbieranie danych faktury.
- Narzedzia lokalne: validate_nip, calculate_line, calculate_totals, format_invoice.
- Logowanie metryk: TTFR, czas calkowity, rundy LLM, tokeny, RAM, ocena jakosci.

## Uruchomienie

1. Zainstaluj zaleznosci:

```bash
uv sync agent.py
```

2. Uruchom:

```bash
uv run agent.py
```

Tryb debug:

```bash
uv agent.py --debug
```

## Wyniki

- Logi raw: results/raw
- Zbiorcze CSV: results/summary.csv
