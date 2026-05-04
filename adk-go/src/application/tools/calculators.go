package tools

import (
	"math"
	"strings"
)

type LineCalculation struct {
	NetTotal   float64 `json:"net_total"`
	VatAmount  float64 `json:"vat_amount"`
	GrossTotal float64 `json:"gross_total"`
	Error      string  `json:"error,omitempty"`
}

type TotalsCalculation struct {
	Net   float64 `json:"net"`
	Vat   float64 `json:"vat"`
	Gross float64 `json:"gross"`
}

func roundTo2Decimals(num float64) float64 {
	return math.Round(num*100) / 100
}

func CalculateLine(quantity float64, unitPriceNet float64, vatRate string) LineCalculation {
	rates := map[string]float64{
		"23%": 0.23, "8%": 0.08, "5%": 0.05, "0%": 0.00, "zw.": 0.00,
	}

	cleanRate := strings.ToLower(strings.ReplaceAll(vatRate, " ", ""))
	rate, exists := rates[cleanRate]
	if !exists {
		return LineCalculation{Error: "Nieznana stawka VAT: " + vatRate}
	}

	netTotal := roundTo2Decimals(quantity * unitPriceNet)
	vatAmount := roundTo2Decimals(netTotal * rate)
	grossTotal := roundTo2Decimals(netTotal + vatAmount)

	return LineCalculation{
		NetTotal:   netTotal,
		VatAmount:  vatAmount,
		GrossTotal: grossTotal,
	}
}

func CalculateTotals(lines []map[string]any) TotalsCalculation {
	var net, vat float64
	for _, l := range lines {
		if n, ok := l["net_total"].(float64); ok {
			net += n
		}
		if v, ok := l["vat_amount"].(float64); ok {
			vat += v
		}
	}
	return TotalsCalculation{
		Net:   roundTo2Decimals(net),
		Vat:   roundTo2Decimals(vat),
		Gross: roundTo2Decimals(net + vat),
	}
}