package infrastructure

import (
	"encoding/json"
	"regexp"
	"strings"
)

func ExtractInvoiceJSON(text string) map[string]any {
	text = strings.ReplaceAll(text, "```json", "")
	text = strings.ReplaceAll(text, "```", "")

	start := strings.Index(text, "{")
	if start == -1 {
		return nil
	}

	re := regexp.MustCompile(`\{[\s\S]*\}`)
	match := re.FindString(text[start:])

	if match == "" {
		return nil
	}

	var result map[string]any
	if err := json.Unmarshal([]byte(match), &result); err != nil {
		return nil
	}

	_, hasInvoice := result["invoice"]
	_, hasSeller := result["seller"]

	if hasInvoice || hasSeller {
		return result
	}

	return nil
}

func EvaluateQuality(log []map[string]any) map[string]any {
	var sb strings.Builder
	for _, entry := range log {
		if entry["role"] == "agent" {
			if content, ok := entry["content"].(string); ok {
				sb.WriteString(strings.ToLower(content) + " ")
			}
		}
	}
	fullText := sb.String()

	checks := map[string]bool{
		"seller_data_correct":      strings.Contains(fullText, "5260308476") && strings.Contains(fullText, "aperture"),
		"buyer_data_correct":       strings.Contains(fullText, "3623981230") && strings.Contains(fullText, "kowalski"),
		"nip_validation_triggered": strings.Contains(fullText, "błędn") || strings.Contains(fullText, "niepoprawn") || strings.Contains(fullText, "poprawn") || strings.Contains(fullText, "sprawdzon"),
		"calculations_correct":     strings.Contains(fullText, "8500") && strings.Contains(fullText, "10455"),
		"invoice_json_returned":    strings.Contains(fullText, "\"invoice\"") && (strings.Contains(fullText, "\"totals\"") || strings.Contains(fullText, "\"financials\"")),
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