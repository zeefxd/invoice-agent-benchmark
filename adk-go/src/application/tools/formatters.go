package tools

import "fmt"

func FormatInvoice(data map[string]any) map[string]any {
	requiredKeys :=[]string{"invoice", "seller", "buyer", "line_items"}
	for _, k := range requiredKeys {
		if _, ok := data[k]; !ok {
			return map[string]any{"error": fmt.Sprintf("Brakujące sekcje w danych wejściowych: %s", k)}
		}
	}

	var linesCalculated []map[string]any
	rawItems, ok := data["line_items"].([]interface{})
	if !ok {
		return map[string]any{"error": "line_items musi być poprawną listą."}
	}

	for _, itemRaw := range rawItems {
		item, ok := itemRaw.(map[string]any)
		if !ok {
			continue
		}

		qty, _ := item["quantity"].(float64)
		price, _ := item["unit_price_net"].(float64)
		vat, _ := item["vat_rate"].(string)

		calc := CalculateLine(qty, price, vat)
		if calc.Error != "" {
			name, _ := item["name"].(string)
			return map[string]any{"error": fmt.Sprintf("Błąd w obliczeniach pozycji '%s': %s", name, calc.Error)}
		}

		item["net_total"] = calc.NetTotal
		item["vat_amount"] = calc.VatAmount
		item["gross_total"] = calc.GrossTotal
		linesCalculated = append(linesCalculated, item)
	}

	totals := CalculateTotals(linesCalculated)

	return map[string]any{
		"invoice":    data["invoice"],
		"seller":     data["seller"],
		"buyer":      data["buyer"],
		"line_items": linesCalculated,
		"totals":     totals,
	}
}