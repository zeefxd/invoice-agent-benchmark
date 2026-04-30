import { LlmAgent, FunctionTool } from "@google/adk";
import { z } from "zod";

import * as Tools from "./tools";

const validateNipTool = new FunctionTool(
  {
    name: "validate_nip",
    parameters: Tools.validateNipSchema,
    description: "Sprawdza poprawność NIP (suma kontrolna). Zwraca obiekt { valid: boolean, message: string }.",
  },
  ({ nip }: Tools.ValidateNipParams) => Tools.validateNip(nip)
);

const calculateLineTool = new FunctionTool(
  {
    name: "calculate_line",
    parameters: Tools.calculateLineSchema,
    description:
      "Oblicza netto, VAT i brutto dla jednej pozycji faktury. Zwraca obiekt z polami net_total, vat_amount, gross_total.",
  },
  ({ quantity, unitPriceNet, vatRate }: Tools.CalculateLineParams) =>
    Tools.calculateLine(quantity, unitPriceNet, vatRate)
);

const calculateTotalsTool = new FunctionTool(
  {
    name: "calculate_totals",
    parameters: Tools.calculateTotalsSchema,
    description:
      "Oblicza sumy netto, VAT i brutto dla wszystkich pozycji faktury.",
  },
  ({ lines }: Tools.CalculateTotalsParams) => Tools.calculateTotals(lines)
);

const formatInvoiceTool = new FunctionTool(
  {
    name: "format_invoice",
    parameters: Tools.formatInvoiceSchema,
    description:
      "Formatuje i zwraca gotowy JSON faktury VAT w restrykcyjnej strukturze. Zwraca fakturę z kluczami: invoice, seller, buyer, line_items, totals.",
  },
  ({ data }: { data: Tools.FormatInvoiceParams }) => Tools.formatInvoice(data)
);

const SYSTEM_PROMPT = `Jesteś profesjonalnym, rzetelnym asystentem do wystawiania faktur VAT w Polsce.
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
- Jeśli zadajesz pytanie użytkownikowi lub odpowiadasz bezpośrednio jemu, ODPOWIEDZ ZWYKŁYM TEKSTEM, a nie poprzez tworzenie JSONa jak przy wywoływaniu funkcji!
- Wywołuj funkcje (formatując jako call tool JSON) tylko wtedy, gdy musisz przeliczyć coś matematycznie albo zwalidować.
- Twoja FINALNA ODPOWIEDŹ po uruchomieniu narzędzia format_invoice to MA BYĆ WYŁĄCZNIE CZYSTY JSON, dokładnie w takiej postaci, jaką przed chwilą zwróciło narzędzie. Żadnego dodatkowego tekstu ani formatowania.`;

export const rootAgent = new LlmAgent({
  name: "invoice_agent",
  model: "ollama_chat/gpt-oss:20b", 
  description: "Agent do wypełniania faktur VAT",
  instruction: SYSTEM_PROMPT,
  tools: [
    validateNipTool,
    calculateLineTool,
    calculateTotalsTool,
    formatInvoiceTool,
  ],
});