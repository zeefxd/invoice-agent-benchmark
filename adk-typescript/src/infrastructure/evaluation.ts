const VAT_RATES: Record<string, number> = {
    "23%": 0.23,
    "8%": 0.08,
    "5%": 0.05,
    "0%": 0.0,
    "zw.": 0.0,
};

function isNonEmptyString(value: unknown): boolean {
    return typeof value === "string" && value.trim().length > 0;
}

function extractJsonCandidates(text: string): any[] {
    const cleanText = text.replace(/```json/g, "").replace(/```/g, "");
    const candidates: any[] = [];

    for (let i = 0; i < cleanText.length; i++) {
        if (cleanText[i] !== "{") {
            continue;
        }

        let depth = 0;
        for (let j = i; j < cleanText.length; j++) {
            if (cleanText[j] === "{") {
                depth += 1;
            } else if (cleanText[j] === "}") {
                depth -= 1;
                if (depth === 0) {
                    const chunk = cleanText.slice(i, j + 1);
                    try {
                        candidates.push(JSON.parse(chunk));
                    } catch {
                    }
                    i = j;
                    break;
                }
            }
        }
    }

    return candidates;
}

export function extractInvoiceJson(text: string): any | null {
    const candidates = extractJsonCandidates(text);
    for (let i = candidates.length - 1; i >= 0; i--) {
        const obj = candidates[i];
        if (obj && typeof obj === "object" && "invoice" in obj && "totals" in obj) {
            return obj;
        }
    }
    return null;
}

function hasInvoiceStructure(invoice: any): boolean {
    if (!invoice || typeof invoice !== "object") {
        return false;
    }

    const requiredRoot = ["invoice", "seller", "buyer", "line_items", "totals"];
    if (!requiredRoot.every((k) => k in invoice)) {
        return false;
    }

    if (!Array.isArray(invoice.line_items) || invoice.line_items.length < 1) {
        return false;
    }

    const parties = [invoice.seller, invoice.buyer];
    for (const party of parties) {
        if (!party || typeof party !== "object") {
            return false;
        }
        if (!isNonEmptyString(party.name) || !isNonEmptyString(party.nip)) {
            return false;
        }
        if (!party.address || typeof party.address !== "object") {
            return false;
        }
        if (!isNonEmptyString(party.address.street) || !isNonEmptyString(party.address.postal_code) || !isNonEmptyString(party.address.city)) {
            return false;
        }
    }

    const lineKeys = ["name", "quantity", "unit", "unit_price_net", "vat_rate", "net_total", "vat_amount", "gross_total"];
    for (const item of invoice.line_items) {
        if (!item || typeof item !== "object") {
            return false;
        }
        if (!lineKeys.every((k) => k in item)) {
            return false;
        }
    }

    return true;
}

function hasCorrectCalculations(invoice: any): boolean {
    if (!hasInvoiceStructure(invoice)) {
        return false;
    }

    let sumNet = 0;
    let sumVat = 0;
    let sumGross = 0;

    for (const item of invoice.line_items) {
        const qty = Number(item.quantity);
        const unitPrice = Number(item.unit_price_net);
        const netTotal = Number(item.net_total);
        const vatAmount = Number(item.vat_amount);
        const grossTotal = Number(item.gross_total);
        const rate = VAT_RATES[String(item.vat_rate).toLowerCase().replace(/\s/g, "")];

        if (![qty, unitPrice, netTotal, vatAmount, grossTotal].every((v) => Number.isFinite(v))) {
            return false;
        }
        if (typeof rate !== "number") {
            return false;
        }

        const expectedNet = Math.round((qty * unitPrice) * 100) / 100;
        const expectedVat = Math.round((expectedNet * rate) * 100) / 100;
        const expectedGross = Math.round((expectedNet + expectedVat) * 100) / 100;

        if (Math.round(netTotal * 100) / 100 !== expectedNet) {
            return false;
        }
        if (Math.round(vatAmount * 100) / 100 !== expectedVat) {
            return false;
        }
        if (Math.round(grossTotal * 100) / 100 !== expectedGross) {
            return false;
        }

        sumNet += netTotal;
        sumVat += vatAmount;
        sumGross += grossTotal;
    }

    const tNet = Number(invoice.totals?.net);
    const tVat = Number(invoice.totals?.vat);
    const tGross = Number(invoice.totals?.gross);
    if (![tNet, tVat, tGross].every((v) => Number.isFinite(v))) {
        return false;
    }

    return (
        Math.round(sumNet * 100) / 100 === Math.round(tNet * 100) / 100
        && Math.round(sumVat * 100) / 100 === Math.round(tVat * 100) / 100
        && Math.round(sumGross * 100) / 100 === Math.round(tGross * 100) / 100
    );
}

function nipValidationUsed(log: any[]): boolean {
    for (const entry of log) {
        if (entry?.role !== "agent") {
            continue;
        }
        const toolCalls = entry?.meta?.tool_calls;
        if (Array.isArray(toolCalls) && toolCalls.includes("validate_nip")) {
            return true;
        }
    }
    return false;
}

export function evaluateQuality(log: any[]): any {
    let invoiceObj: any | null = null;
    for (let i = log.length - 1; i >= 0; i--) {
        const entry = log[i];
        if (entry?.role !== "agent" || typeof entry?.content !== "string") {
            continue;
        }
        invoiceObj = extractInvoiceJson(entry.content);
        if (invoiceObj) {
            break;
        }
    }

    const structureOk = hasInvoiceStructure(invoiceObj);
    const checks = {
        seller_data_correct: structureOk,
        buyer_data_correct: structureOk,
        nip_validation_triggered: nipValidationUsed(log),
        calculations_correct: hasCorrectCalculations(invoiceObj),
        invoice_json_returned: structureOk,
    };

    const values = Object.values(checks);
    const score = (values.filter(Boolean).length / values.length) * 5;

    return {
        checks,
        auto_score_0_5: Number(score.toFixed(2)),
    };
}