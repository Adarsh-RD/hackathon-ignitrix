"""
returnX AI — Tax Advisor Agent (LangChain + RAG)
Uses RAG to retrieve relevant tax provisions before advising.
Combines: LangChain LLM + RAG retrieval + TaxCalculator tool.
"""

import json
from langchain_groq import ChatGroq
from agents.base_agent import BaseAgent
from tools.tax_calculator import TaxCalculator


class TaxAdvisorAgent(BaseAgent):
    """Agent that uses RAG + tools + LLM to compute tax strategy."""

    def __init__(self, llm: ChatGroq = None, knowledge_base=None):
        super().__init__(
            name="TaxAdvisorAgent",
            role="Indian Tax Advisor for Gig Workers",
            llm=llm,
        )
        self.tax_tool = TaxCalculator()
        self.knowledge_base = knowledge_base  # RAG component

    def get_system_prompt(self) -> str:
        return """You are an expert Indian tax advisor agent for gig workers.

TASK: Given the user's income/expense data AND retrieved tax knowledge, compute tax obligations and provide strategic advice.

You will receive:
1. The user's financial data
2. Relevant Indian tax provisions retrieved from our knowledge base (RAG)
3. Pre-computed tax metrics from a deterministic tool

Use ALL three sources to provide accurate advice.

OUTPUT FORMAT — Return ONLY this JSON:
{
  "agent": "TaxAdvisorAgent",
  "reasoning": "Step-by-step tax reasoning referencing specific sections",
  "annual_income_projected": <number>,
  "annual_expenses_projected": <number>,
  "tds_estimated": <number>,
  "taxable_under_44ad": <number>,
  "tax_payable_estimated": <number>,
  "effective_tax_rate": "<percentage>",
  "regime_recommended": "old" or "new",
  "recommendations": ["tip1", "tip2", "tip3"],
  "old_regime_tax": <number>,
  "new_regime_tax": <number>
}"""

    def run(self, input_data: dict) -> dict:
        parsed = input_data.get("parsed", {})
        historical = input_data.get("historical", {})

        total_income = historical.get("total_income_amt", 0)
        total_expenses = historical.get("total_expense_amt", 0)

        # ── ReAct Step 1: THINK ──
        self.think(f"Analysing tax for ₹{total_income} income, ₹{total_expenses} expenses")

        # ── ReAct Step 2: ACT — Use TaxCalculator tool ──
        self.act("Computing base tax metrics", tool_name="tax_calculator")
        base_tax = self.tax_tool.compute(
            total_income=total_income,
            total_expenses=total_expenses,
        )
        self.observe(f"Tool result: TDS=₹{base_tax['tds']}, 44AD=₹{base_tax['taxable_44ad']}")

        # ── ReAct Step 3: ACT — RAG retrieval ──
        rag_context = ""
        if self.knowledge_base:
            self.act("Retrieving relevant tax provisions", tool_name="rag_retrieval")
            query = f"Tax rules for gig worker earning ₹{total_income} from platforms like Swiggy Zomato with expenses ₹{total_expenses} on fuel and recharge"
            rag_context = self.knowledge_base.retrieve(query, k=4)
            self.observe(f"RAG retrieved {len(rag_context)} chars of tax knowledge")
        else:
            self.think("No RAG knowledge base available, using LLM knowledge only")

        # ── ReAct Step 4: ACT — Call LLM with all context ──
        context = f"""
FINANCIAL DATA:
- Income entries: {len(historical.get('total_income', []))}
- Expense entries: {len(historical.get('total_expenses', []))}
- Total income: ₹{total_income}
- Total expenses: ₹{total_expenses}
- Income by platform: {json.dumps(historical.get('income_by_platform', {}))}
- Expenses by category: {json.dumps(historical.get('expense_by_category', {}))}

PRE-COMPUTED TAX (from TaxCalculator tool):
- TDS at 1%: ₹{base_tax['tds']}
- 44AD taxable at 6%: ₹{base_tax['taxable_44ad']}
- Net income: ₹{base_tax['net_income']}
- Annual projected income: ₹{base_tax['annual_income_projected']}
- Tax under old regime (tool): ₹{base_tax['tax_regular']}
- Tax under 44AD (tool): ₹{base_tax['tax_on_44ad']}
- Tool recommended: {base_tax['regime_recommended']}

RETRIEVED TAX KNOWLEDGE (RAG):
{rag_context if rag_context else 'No RAG context available.'}

Provide detailed tax analysis using the above data and retrieved knowledge."""

        result = self.call_llm(context)

        result.setdefault("tds_estimated", base_tax["tds"])
        result.setdefault("taxable_under_44ad", base_tax["taxable_44ad"])
        result.setdefault("old_regime_tax", base_tax["tax_regular"])
        result.setdefault("new_regime_tax", base_tax["tax_on_44ad"])

        return {
            "agent": self.name,
            **result,
            "tool_computed": base_tax,
            "rag_used": bool(rag_context),
        }
