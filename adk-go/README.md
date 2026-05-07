# ADK Go - Invoice Agent Benchmark

Implementacja agenta fakturowego VAT w Google ADK (Go).

## Zakres

- Konwersacja i zbieranie danych do faktury VAT.
- Narzedzia lokalne: validate_nip, calculate_line, calculate_totals, format_invoice.
- Zapis metryk benchmarku do JSON i CSV.

## Uruchomienie

```bash
go run ./agent.go
```

Tryb debug:

```bash
go run ./agent.go --debug
```

## Wyniki

- Logi raw: results/raw
- Zbiorcze CSV: results/summary.csv
