"""
returnX AI — SMS Parser Agent
Extracts structured income/expense data from raw SMS messages.
Uses ReAct reasoning to classify each transaction.
"""

from langchain_groq import ChatGroq
from agents.base_agent import BaseAgent


class SmsParserAgent(BaseAgent):
    """Agent that parses raw SMS text into structured financial transactions."""

    def __init__(self, llm: ChatGroq = None):
        super().__init__(
            name="SmsParserAgent",
            role="SMS Transaction Parser",
            llm=llm,
        )

    def get_system_prompt(self) -> str:
        return """You are an expert SMS transaction parser agent.

TASK: Analyse the raw SMS messages provided by the user and extract ALL financial transactions.

REASONING STEPS (follow these internally):
1. SCAN each message for monetary amounts (₹, Rs, INR patterns)
2. CLASSIFY each transaction as INCOME (credit/transfer/deposit) or EXPENSE (debit/paid/charged)
3. IDENTIFY the platform/category:
   - Income platforms: Swiggy, Zomato, Rapido, Ola, Uber, Zepto, Blinkit, Dunzo, Porter, BigBasket
   - Expense categories: Petrol/Fuel (HPCL, BPCL, IOC, HP), Phone Recharge (Airtel, Jio, Vi), Internet, Vehicle Service/Maintenance, Insurance, Toll
4. EXTRACT the date if mentioned (any format)
5. VALIDATE amounts are positive numbers

OUTPUT FORMAT — Return ONLY this JSON:
{
  "agent": "SmsParserAgent",
  "reasoning": "Brief explanation of what you found",
  "transactions_found": <number>,
  "income": [{ "platform": "...", "amount": <number>, "date": "..." }],
  "expenses": [{ "category": "...", "amount": <number>, "date": "..." }]
}

RULES:
- If date not found, use "unknown"
- If platform/category unclear, use best guess with "(estimated)" suffix
- Never hallucinate transactions that aren't in the SMS
- Return empty arrays if nothing found"""

    def run(self, input_data: dict) -> dict:
        """
        Parse SMS messages and extract transactions.

        Args:
            input_data: {"sms_text": str}

        Returns:
            {"income": [...], "expenses": [...], "reasoning": str}
        """
        sms_text = input_data.get("sms_text", "")

        # ReAct: Think
        self.think(f"Received {len(sms_text)} characters of SMS text to parse")
        self.think("Will scan for income credits and expense debits")

        # ReAct: Act — call LLM
        result = self.call_llm(sms_text)

        # ReAct: Observe
        income = result.get("income", [])
        expenses = result.get("expenses", [])
        self.observe(f"Extracted {len(income)} income + {len(expenses)} expense transactions")

        return {
            "agent": self.name,
            "reasoning": result.get("reasoning", ""),
            "income": income,
            "expenses": expenses,
            "transactions_found": len(income) + len(expenses),
        }
