package infrastructure

import (
	"encoding/json"
	"math"
	"strings"
)

var vatRates = map[string]float64{
	"23%": 0.23,
	"8%":  0.08,
	"5%":  0.05,
	"0%":  0.0,
	"zw.": 0.0,
}

func ExtractInvoiceJSON(text string) map[string]any {
	text = strings.ReplaceAll(text, "```json", "")
	text = strings.ReplaceAll(text, "```", "")

	var candidates []map[string]any
	for i := 0; i < len(text); i++ {
		if text[i] != '{' {
			continue
		}
		depth := 0
		for j := i; j < len(text); j++ {
			if text[j] == '{' {
				depth++
			} else if text[j] == '}' {
				depth--
				if depth == 0 {
					chunk := text[i : j+1]
					var parsed map[string]any
					if err := json.Unmarshal([]byte(chunk), &parsed); err == nil {
						candidates = append(candidates, parsed)
					}
					i = j
					break
				}
			}
		}
	}

	for i := len(candidates) - 1; i >= 0; i-- {
		obj := candidates[i]
		if _, ok := obj["invoice"]; ok {
			if _, okTotals := obj["totals"]; okTotals {
				return obj
			}
		}
	}

	return nil
}

func isNonEmptyString(v any) bool {
	s, ok := v.(string)
	return ok && strings.TrimSpace(s) != ""
}

func asMap(v any) (map[string]any, bool) {
	m, ok := v.(map[string]any)
	return m, ok
}

func asSlice(v any) ([]any, bool) {
	s, ok := v.([]any)
	return s, ok
}

func asFloat(v any) (float64, bool) {
	value, ok := v.(float64)
	return value, ok
}

func hasInvoiceStructure(invoice map[string]any) bool {
	if invoice == nil {
		return false
	}

	required := []string{"invoice", "seller", "buyer", "line_items", "totals"}
	for _, key := range required {
		if _, ok := invoice[key]; !ok {
			return false
		}
	}

	seller, ok := asMap(invoice["seller"])
	if !ok {
		return false
	}
	buyer, ok := asMap(invoice["buyer"])
	if !ok {
		return false
	}
	lineItems, ok := asSlice(invoice["line_items"])
	if !ok || len(lineItems) < 1 {
		return false
	}
	if _, ok := asMap(invoice["totals"]); !ok {
		return false
	}

	for _, party := range []map[string]any{seller, buyer} {
		if !isNonEmptyString(party["name"]) || !isNonEmptyString(party["nip"]) {
			return false
		}
		address, ok := asMap(party["address"])
		if !ok {
			return false
		}
		if !isNonEmptyString(address["street"]) || !isNonEmptyString(address["postal_code"]) || !isNonEmptyString(address["city"]) {
			return false
		}
	}

	requiredLine := []string{"name", "quantity", "unit", "unit_price_net", "vat_rate", "net_total", "vat_amount", "gross_total"}
	for _, itemRaw := range lineItems {
		item, ok := asMap(itemRaw)
		if !ok {
			return false
		}
		for _, key := range requiredLine {
			if _, ok := item[key]; !ok {
				return false
			}
		}
	}

	return true
}

func round2(v float64) float64 {
	return math.Round(v*100) / 100
}

func hasCorrectCalculations(invoice map[string]any) bool {
	if !hasInvoiceStructure(invoice) {
		return false
	}

	lineItems, _ := asSlice(invoice["line_items"])
	totals, _ := asMap(invoice["totals"])

	sumNet := 0.0
	sumVat := 0.0
	sumGross := 0.0

	for _, itemRaw := range lineItems {
		item, _ := asMap(itemRaw)

		qty, okQty := asFloat(item["quantity"])
		unitPrice, okPrice := asFloat(item["unit_price_net"])
		netTotal, okNet := asFloat(item["net_total"])
		vatAmount, okVat := asFloat(item["vat_amount"])
		grossTotal, okGross := asFloat(item["gross_total"])
		vatRate, okRate := item["vat_rate"].(string)
		if !okQty || !okPrice || !okNet || !okVat || !okGross || !okRate {
			return false
		}

		rate, exists := vatRates[strings.ToLower(strings.ReplaceAll(vatRate, " ", ""))]
		if !exists {
			return false
		}

		expectedNet := round2(qty * unitPrice)
		expectedVat := round2(expectedNet * rate)
		expectedGross := round2(expectedNet + expectedVat)

		if round2(netTotal) != expectedNet || round2(vatAmount) != expectedVat || round2(grossTotal) != expectedGross {
			return false
		}

		sumNet += netTotal
		sumVat += vatAmount
		sumGross += grossTotal
	}

	tNet, okNet := asFloat(totals["net"])
	tVat, okVat := asFloat(totals["vat"])
	tGross, okGross := asFloat(totals["gross"])
	if !okNet || !okVat || !okGross {
		return false
	}

	return round2(sumNet) == round2(tNet) && round2(sumVat) == round2(tVat) && round2(sumGross) == round2(tGross)
}

func nipValidationUsed(log []map[string]any) bool {
	for _, entry := range log {
		if entry["role"] != "agent" {
			continue
		}
		meta, ok := entry["meta"].(map[string]any)
		if !ok {
			continue
		}
		calls, ok := meta["tool_calls"].([]any)
		if !ok {
			continue
		}
		for _, c := range calls {
			if name, ok := c.(string); ok && name == "validate_nip" {
				return true
			}
		}
	}
	return false
}

func EvaluateQuality(log []map[string]any) map[string]any {
	var invoiceObj map[string]any
	for i := len(log) - 1; i >= 0; i-- {
		entry := log[i]
		if entry["role"] != "agent" {
			continue
		}
		content, ok := entry["content"].(string)
		if !ok {
			continue
		}
		parsed := ExtractInvoiceJSON(content)
		if parsed != nil {
			invoiceObj = parsed
			break
		}
	}

	structureOk := hasInvoiceStructure(invoiceObj)

	checks := map[string]bool{
		"seller_data_correct":      structureOk,
		"buyer_data_correct":       structureOk,
		"nip_validation_triggered": nipValidationUsed(log),
		"calculations_correct":     hasCorrectCalculations(invoiceObj),
		"invoice_json_returned":    structureOk,
	}

	score := 0.0
	for _, passed := range checks {
		if passed {
			score += 1.0
		}
	}
	score = (score / float64(len(checks))) * 5.0

	return map[string]any{
		"checks":         checks,
		"auto_score_0_5": score,
	}
}