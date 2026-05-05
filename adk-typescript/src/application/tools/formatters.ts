import { calculateLine, calculateTotals } from './calculators';

export function formatInvoice(data: any): any {
    if (!data || typeof data !== 'object') {
        return { error: "Dane wejściowe muszą być obiektem JSON." };
    }

    const requiredKeys = ['invoice', 'seller', 'buyer', 'line_items'];
    for (const key of requiredKeys) {
        if (!(key in data)) {
            return { error: `Brakujące sekcje w danych wejściowych: ${key}` };
        }
    }

    if (!Array.isArray(data.line_items)) {
        return { error: "line_items musi być poprawną listą." };
    }

    const linesCalculated: any[] = [];

    for (const item of data.line_items) {
        if (!item || typeof item !== 'object') continue;

        const qty = typeof item.quantity === 'number' ? item.quantity : parseFloat(item.quantity) || 0;
        const price = typeof item.unit_price_net === 'number' ? item.unit_price_net : parseFloat(item.unit_price_net) || 0;
        const vatRate = typeof item.vat_rate === 'string' ? item.vat_rate : String(item.vat_rate || "23%");

        const calc = calculateLine(qty, price, vatRate);

        const calculatedItem = { ...item };
        calculatedItem.net_total = calc.net_total;
        calculatedItem.vat_amount = calc.vat_amount;
        calculatedItem.gross_total = calc.gross_total;

        linesCalculated.push(calculatedItem);
    }

    const totals = calculateTotals(linesCalculated);

    return {
        invoice: data.invoice,
        seller: data.seller,
        buyer: data.buyer,
        line_items: linesCalculated,
        totals: {
            net: totals.total_net,
            vat: totals.total_vat,
            gross: totals.total_gross
        }
    };
}