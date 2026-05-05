export function extractInvoiceJson(text: string): any | null {
    let cleanText = text.replace(/```json/g, "").replace(/```/g, "");

    const start = cleanText.indexOf("{");
    if (start === -1) {
        return null;
    }

    const regexEnd = /\{[\s\S]*\}$/;
    let match = cleanText.substring(start).match(regexEnd);
    let jsonString = match ? match[0] : "";

    if (!jsonString) {
        const regexAlternative = /\{[\s\S]*\}/;
        match = cleanText.substring(start).match(regexAlternative);
        jsonString = match ? match[0] : "";
        if (!jsonString) {
            return null;
        }
    }

    try {
        const result = JSON.parse(jsonString);
        const hasInvoice = result.hasOwnProperty("invoice");
        const hasSeller = result.hasOwnProperty("seller");

        if (hasInvoice || hasSeller) {
            return result;
        }
        return null;
    } catch (err) {
        return null;
    }
}

export function evaluateQuality(log: any[]): any {
    let sb = "";
    for (const entry of log) {
        if (entry.role === "agent" && typeof entry.content === "string") {
            sb += entry.content.toLowerCase() + " ";
        }
    }

    const checks = {
        seller_data_correct: sb.includes("5260308476") && sb.includes("aperture"),
        buyer_data_correct: sb.includes("3623981230") && sb.includes("kowalski"),
        nip_validation_triggered: sb.includes("błędn") || sb.includes("niepoprawn") || sb.includes("poprawn") || sb.includes("sprawdzon"),
        calculations_correct: sb.includes("8500") && sb.includes("10455"),
        invoice_json_returned: sb.includes("\"invoice\"") && (sb.includes("\"totals\"") || sb.includes("\"financials\""))
    };

    let score = 0.0;
    const keys = Object.keys(checks);
    for (const key of keys) {
        if ((checks as any)[key]) {
            score += 1.0;
        }
    }
    score = (score / keys.length) * 5.0;

    return {
        checks: checks,
        auto_score_0_5: score
    };
}