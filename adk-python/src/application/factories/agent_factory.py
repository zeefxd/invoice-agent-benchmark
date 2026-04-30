from google.adk.agents import Agent
from src.domain.constants import INVOICE_AGENT_SYSTEM_PROMPT
from src.application.tools.validators import validate_nip
from src.application.tools.calculators import calculate_line, calculate_totals
from src.application.tools.formatters import format_invoice

class AgentBuilder:
    @staticmethod
    def build(model_identifier: str) -> Agent:
        return Agent(
            name="invoice_agent",
            model=model_identifier,
            description="Agent do wypełniania faktur VAT (Benchmark)",
            instruction=INVOICE_AGENT_SYSTEM_PROMPT,
            tools=[validate_nip, calculate_line, calculate_totals, format_invoice],
        )