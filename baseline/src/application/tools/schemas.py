TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "validate_nip",
            "description": "Sprawdza poprawność numeru NIP. Zwraca true jeśli NIP jest poprawny.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nip": {"type": "string", "description": "10-cyfrowy numer NIP"}
                },
                "required": ["nip"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_line",
            "description": "Oblicza kwotę netto, VAT i brutto dla pojedynczej pozycji na fakturze.",
            "parameters": {
                "type": "object",
                "properties": {
                    "qty": {"type": "number", "description": "Ilość towaru/usługi"},
                    "price": {"type": "number", "description": "Cena netto jednostkowa"},
                    "vat_rate": {"type": "string", "description": "Stawka VAT (np. '23%', '8%', 'zw.')"},
                },
                "required": ["qty", "price", "vat_rate"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_totals",
            "description": "Oblicza całkowitą wartość netto, VAT i brutto dla wszystkich pozycji faktury.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lines": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "net_total": {"type": "number"},
                                "vat_amount": {"type": "number"},
                                "gross_total": {"type": "number"},
                            },
                        },
                    }
                },
                "required": ["lines"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "format_invoice",
            "description": "Zapisuje fakturę. Użyj tego narzędzia TYLKO na samym końcu, gdy posiadasz absolutnie wszystkie dane wymagane do faktury.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "object",
                        "description": "Kompletny JSON faktury zgodnie ze schematem",
                    }
                },
                "required": ["data"],
            },
        },
    },
]
