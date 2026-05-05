export function validateNip(nip: string): { is_valid: boolean; error_msg?: string; normalized_nip?: string } {
    if (!nip) {
        return { is_valid: false, error_msg: "NIP nie może być pusty" };
    }

    const n = nip.replace(/[\s-]/g, "");

    if (!/^\d{10}$/.test(n)) {
        return { is_valid: false, error_msg: "NIP musi składać się dokładnie z 10 cyfr" };
    }

    const weights = [6, 5, 7, 2, 3, 4, 5, 6, 7];
    let sum = 0;
    
    for (let i = 0; i < 9; i++) {
        sum += parseInt(n[i], 10) * weights[i];
    }
    
    const controlDigit = sum % 11;
    
    if (controlDigit !== parseInt(n[9], 10)) {
        return { is_valid: false, error_msg: "Błędna suma kontrolna NIP" };
    }

    return { is_valid: true, normalized_nip: n };
}