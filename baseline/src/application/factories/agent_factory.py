import os

from openai import OpenAI

from src.domain.constants import OLLAMA_BASE_URL
from src.application.tools.validators import validate_nip
from src.application.tools.calculators import calculate_line, calculate_totals
from src.application.tools.formatters import format_invoice
from src.application.tools.schemas import TOOLS_SCHEMA


class AgentBuilder:
    @staticmethod
    def build(model_identifier: str) -> dict:
        return {
            "client": OpenAI(
                base_url=os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL),
                api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
            ),
            "model": model_identifier,
            "tools_schema": TOOLS_SCHEMA,
            "available_tools": {
                "validate_nip": validate_nip,
                "calculate_line": calculate_line,
                "calculate_totals": calculate_totals,
                "format_invoice": format_invoice,
            },
        }
