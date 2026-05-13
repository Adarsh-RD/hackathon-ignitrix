"""
returnX AI — Agent Orchestrator (LangChain + RAG + Multi-Agent)

Frameworks used:
- LangChain:  ChatGroq LLM, prompt management, message schema
- RAG:        ChromaDB vector store + HuggingFace embeddings
- Multi-Agent: Custom orchestrator chaining 3 specialist agents

Pipeline: SmsParser → TaxAdvisor (RAG + Tool) → Insights
"""

import time
from langchain_groq import ChatGroq

from agents.sms_parser import SmsParserAgent
from agents.tax_advisor import TaxAdvisorAgent
from agents.insights_agent import InsightsAgent
from rag.knowledge_base import TaxKnowledgeBase


class AgentOrchestrator:
    """
    Multi-Agent Pipeline Controller.

    Architecture:
    ┌──────────────────────────────────────────────────────┐
    │  ORCHESTRATOR                                        │
    │                                                      │
    │  LangChain ChatGroq ──► shared across all agents     │
    │                                                      │
    │  [1] SmsParserAgent                                  │
    │       └─ LangChain LLM call                          │
    │       └─ Output: {income[], expenses[]}              │
    │                │                                     │
    │                ▼                                     │
    │  [2] TaxAdvisorAgent                                 │
    │       └─ Tool: TaxCalculator (deterministic)         │
    │       └─ RAG: ChromaDB retrieval (tax_rules.txt)     │
    │       └─ LangChain LLM call (with RAG context)       │
    │       └─ Output: tax strategy + recommendations      │
    │                │                                     │
    │                ▼                                     │
    │  [3] InsightsAgent                                   │
    │       └─ LangChain LLM call                          │
    │       └─ Output: 5 actionable insights               │
    │                                                      │
    │  Memory: AgentMemory (persistent JSON state)         │
    └──────────────────────────────────────────────────────┘
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

        # LangChain LLM — shared by all agents
        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=2048,
        )

        # RAG Knowledge Base
        self.knowledge_base = TaxKnowledgeBase()

        # Initialize agents with LangChain LLM
        self.parser = SmsParserAgent(llm=self.llm)
        self.tax_advisor = TaxAdvisorAgent(llm=self.llm, knowledge_base=self.knowledge_base)
        self.insights = InsightsAgent(llm=self.llm)

        self.pipeline_log = []

    def run(self, sms_text: str, accumulated: dict) -> dict:
        """Execute the full multi-agent pipeline."""
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"  ORCHESTRATOR: Starting Multi-Agent Pipeline")
        print(f"  Framework: LangChain + RAG + Multi-Agent")
        print(f"  LLM: Llama 3.3 70B via Groq")
        print(f"  RAG: ChromaDB + HuggingFace Embeddings")
        print(f"  SMS: {len(sms_text)} chars")
        print(f"{'='*60}\n")

        # ── AGENT 1: SMS Parser ──
        print(f"[Agent 1/3] SmsParserAgent (LangChain LLM)...")
        parse_result = self.parser.run({"sms_text": sms_text})
        self.pipeline_log.append({
            "step": 1, "agent": "SmsParserAgent",
            "status": "done",
            "transactions": parse_result.get("transactions_found", 0),
        })

        # Merge with history
        merged_income = accumulated.get("total_income", []) + parse_result.get("income", [])
        merged_expenses = accumulated.get("total_expenses", []) + parse_result.get("expenses", [])

        income_by_platform = {}
        for item in merged_income:
            key = (item.get("platform") or "Other").strip()
            income_by_platform[key] = income_by_platform.get(key, 0) + float(item.get("amount", 0))

        expense_by_category = {}
        for item in merged_expenses:
            key = (item.get("category") or "Other").strip()
            expense_by_category[key] = expense_by_category.get(key, 0) + float(item.get("amount", 0))

        total_income_amt = sum(float(i.get("amount", 0)) for i in merged_income)
        total_expense_amt = sum(float(i.get("amount", 0)) for i in merged_expenses)

        historical = {
            "total_income": merged_income,
            "total_expenses": merged_expenses,
            "total_income_amt": total_income_amt,
            "total_expense_amt": total_expense_amt,
            "income_by_platform": income_by_platform,
            "expense_by_category": expense_by_category,
        }

        # ── AGENT 2: Tax Advisor (RAG + Tool + LLM) ──
        print(f"\n[Agent 2/3] TaxAdvisorAgent (RAG + TaxCalculator + LLM)...")
        tax_result = self.tax_advisor.run({
            "parsed": parse_result,
            "historical": historical,
        })
        self.pipeline_log.append({
            "step": 2, "agent": "TaxAdvisorAgent",
            "status": "done",
            "regime": tax_result.get("regime_recommended", ""),
            "rag_used": tax_result.get("rag_used", False),
        })

        # ── AGENT 3: Insights ──
        print(f"\n[Agent 3/3] InsightsAgent (LangChain LLM)...")
        insights_result = self.insights.run({
            "historical": historical,
            "tax_analysis": tax_result,
        })
        self.pipeline_log.append({
            "step": 3, "agent": "InsightsAgent",
            "status": "done",
            "insights_count": len(insights_result.get("insights", [])),
        })

        elapsed = round(time.time() - start_time, 1)
        print(f"\n{'='*60}")
        print(f"  PIPELINE COMPLETE in {elapsed}s")
        print(f"  Transactions: {parse_result.get('transactions_found', 0)}")
        print(f"  RAG used: {tax_result.get('rag_used', False)}")
        print(f"  Insights: {len(insights_result.get('insights', []))}")
        print(f"{'='*60}\n")

        return {
            "income": parse_result.get("income", []),
            "expenses": parse_result.get("expenses", []),
            "parser_reasoning": parse_result.get("reasoning", ""),
            "tax_analysis": tax_result,
            "insights": insights_result.get("insights", []),
            "agent_log": self.pipeline_log,
            "pipeline_duration": elapsed,
            "agents_used": ["SmsParserAgent", "TaxAdvisorAgent", "InsightsAgent"],
            "frameworks": ["LangChain", "RAG (ChromaDB)", "Multi-Agent"],
        }
