# ADK TypeScript - Invoice Agent Benchmark

Implementacja agenta fakturowego VAT w Google ADK (TypeScript).

## Zakres

- Konwersacja i zbieranie danych do faktury VAT.
- Narzedzia lokalne: validate_nip, calculate_line, calculate_totals, format_invoice.
- Rejestrowanie metryk benchmarkowych.

## Uruchomienie

1. Zainstaluj zaleznosci:

```bash
npm install
```

2. Uruchom:

```bash
npx ts-node agent.ts
```

Tryb debug:

```bash
npx ts-node agent.ts --debug
```

## Wyniki

- Logi raw: results/raw
- Zbiorcze CSV: results/summary.csv
