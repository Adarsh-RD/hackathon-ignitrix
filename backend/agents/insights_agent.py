"""
returnX AI — Insights Agent
Generates actionable financial insights from accumulated data.
Uses the output of both Parser and Tax agents.
"""

import json
from langchain_groq import ChatGroq
from agents.base_agent import BaseAgent


class InsightsAgent(BaseAgent):
    """Agent that generates personalised financial insights."""

    def __init__(self, llm: ChatGroq = None):
        super().__init__(
            name="InsightsAgent",
            role="Financial Insights Generator",
            llm=llm,
        )

    def get_system_prompt(self) -> str:
        return """You are a financial insights agent for Indian gig workers.

TASK: Analyse the user's income/expense patterns and generate exactly 5 actionable insights.

INSIGHT TYPES TO GENERATE:
1. EARNING PATTERN: Which platform pays most, trends, concentration risk
2. EXPENSE ALERT: Biggest expense category, overspending warnings
3. TAX TIP: Specific deduction they might be missing
4. SAVINGS OPPORTUNITY: How much they could save with better expense tracking
5. FINANCIAL HEALTH: Overall assessment (expense-to-income ratio, diversification)

OUTPUT FORMAT — Return ONLY this JSON:
{
  "agent": "InsightsAgent",
  "insights": [
    {
      "type": "earning_pattern" | "expense_alert" | "tax_tip" | "savings" | "health",
      "icon": "star" | "warning" | "lightbulb" | "savings" | "favorite",
      "color": "green" | "red" | "blue" | "amber" | "green",
      "title": "Short title",
      "description": "Detailed actionable insight (1-2 sentences)"
    }
  ]
}

RULES:
- Be specific with numbers, not vague
- Reference actual platforms/categories from the data
- Every insight must be actionable
- Use Indian tax context (mention relevant sections)"""

    def run(self, input_data: dict) -> dict:
        """
        Generate insights from all accumulated data.

        Args:
            input_data: {
                "historical": {...},
                "tax_analysis": {...}
            }

        Returns:
            {"insights": [...]}
        """
        historical = input_data.get("historical", {})
        tax_analysis = input_data.get("tax_analysis", {})

        total_inc = historical.get("total_income_amt", 0)
        total_exp = historical.get("total_expense_amt", 0)

        # ReAct: Think
        self.think(f"Generating insights for ₹{total_inc} income, ₹{total_exp} expenses")
        self.think(f"Income from {len(historical.get('income_by_platform', {}))} platforms")

        # ReAct: Act
        context = f"""
USER'S FINANCIAL DATA:
- Total Income: ₹{total_inc}
- Total Expenses: ₹{total_exp}
- Net Income: ₹{total_inc - total_exp}
- Expense Ratio: {((total_exp / total_inc) * 100) if total_inc > 0 else 0:.1f}%

INCOME BY PLATFORM: {json.dumps(historical.get('income_by_platform', {}))}
EXPENSES BY CATEGORY: {json.dumps(historical.get('expense_by_category', {}))}

TAX ANALYSIS:
- Projected Annual Income: ₹{tax_analysis.get('annual_income_projected', 0)}
- TDS Estimated: ₹{tax_analysis.get('tds_estimated', 0)}
- Taxable under 44AD: ₹{tax_analysis.get('taxable_under_44ad', 0)}
- Recommended Regime: {tax_analysis.get('regime_recommended', 'new')}

Generate 5 specific, actionable insights."""

        result = self.call_llm(context)
        insights = result.get("insights", [])

        self.observe(f"Generated {len(insights)} insights")

        return {
            "agent": self.name,
            "insights": insights,
        }
