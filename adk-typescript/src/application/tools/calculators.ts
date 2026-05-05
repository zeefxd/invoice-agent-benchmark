interface LineCalculation {
    net_total: number;
    vat_amount: number;
    gross_total: number;
}

export function calculateLine(quantity: number, unitPriceNet: number, vatRate: string): LineCalculation {
    const netTotal = quantity * unitPriceNet;
    let vatMultiplier = 0.0;
    
    if (vatRate !== "zw" && vatRate !== "np") {
        const cleanRate = vatRate.replace('%', '');
        vatMultiplier = parseFloat(cleanRate) / 100.0;
    }
    
    const vatAmount = Math.round((netTotal * vatMultiplier) * 100) / 100;
    const grossTotal = Math.round((netTotal + vatAmount) * 100) / 100;
    
    return {
        net_total: netTotal,
        vat_amount: vatAmount,
        gross_total: grossTotal
    };
}

interface TotalsCalculation {
    total_net: number;
    total_vat: number;
    total_gross: number;
}

export function calculateTotals(lines: any[]): TotalsCalculation {
    let totalNet = 0.0;
    let totalVat = 0.0;
    
    if (lines && Array.isArray(lines)) {
        for (const line of lines) {
            totalNet += line.net_total || 0;
            totalVat += line.vat_amount || 0;
        }
    }
    
    const totalGross = totalNet + totalVat;
    
    return {
        total_net: Math.round(totalNet * 100) / 100,
        total_vat: Math.round(totalVat * 100) / 100,
        total_gross: Math.round(totalGross * 100) / 100
    };
}