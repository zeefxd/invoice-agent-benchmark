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
                        "properties": {
                            "invoice": {
                                "type": "object",
                                "properties": {
                                    "issue_date": {"type": "string"},
                                    "sale_date": {"type": "string"},
                                    "payment_due_date": {"type": "string"},
                                    "payment_method": {"type": "string"},
                                    "bank_account": {"type": "string"},
                                },
                                "required": ["issue_date", "sale_date", "payment_due_date", "payment_method"],
                            },
                            "seller": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "nip": {"type": "string"},
                                    "address": {
                                        "type": "object",
                                        "properties": {
                                            "street": {"type": "string"},
                                            "postal_code": {"type": "string"},
                                            "city": {"type": "string"},
                                        },
                                        "required": ["street", "postal_code", "city"],
                                    },
                                },
                                "required": ["name", "nip", "address"],
                            },
                            "buyer": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "nip": {"type": "string"},
                                    "address": {
                                        "type": "object",
                                        "properties": {
                                            "street": {"type": "string"},
                                            "postal_code": {"type": "string"},
                                            "city": {"type": "string"},
                                        },
                                        "required": ["street", "postal_code", "city"],
                                    },
                                },
                                "required": ["name", "nip", "address"],
                            },
                            "line_items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "quantity": {"type": "number"},
                                        "unit": {"type": "string"},
                                        "unit_price_net": {"type": "number"},
                                        "vat_rate": {"type": "string"},
                                    },
                                    "required": ["name", "quantity", "unit", "unit_price_net", "vat_rate"],
                                },
                            },
                        },
                        "required": ["invoice", "seller", "buyer", "line_items"],
                    }
                },
                "required": ["data"],
            },
        },
    },
]
