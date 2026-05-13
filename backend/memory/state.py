"""
returnX AI — Agent Memory / State Manager
Manages persistent state across agent pipeline runs.
Stores accumulated income, expenses, insights, and agent logs.
"""

import json
import os
from datetime import datetime

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "state.json")


class AgentMemory:
    """
    Persistent memory store for the agentic system.
    Stores accumulated transactions, tax analysis, and insights.
    """

    def __init__(self):
        self.state = {
            "income": [],
            "expenses": [],
            "insights": [],
            "tax_analysis": {},
            "agent_logs": [],
            "session_count": 0,
        }
        self._load()

    def _load(self):
        """Load state from disk."""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
                print(f"[Memory] Loaded state: {len(self.state.get('income', []))}i / {len(self.state.get('expenses', []))}e")
        except Exception as e:
            print(f"[Memory] Could not load state: {e}")

    def save(self):
        """Persist state to disk."""
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            print(f"[Memory] State saved")
        except Exception as e:
            print(f"[Memory] Could not save state: {e}")

    def get_accumulated(self) -> dict:
        """Return accumulated data for agents."""
        return {
            "total_income": self.state.get("income", []),
            "total_expenses": self.state.get("expenses", []),
        }

    def add_results(self, pipeline_result: dict):
        """Merge pipeline results into memory."""
        # Add new income
        new_income = pipeline_result.get("income", [])
        self.state["income"].extend(new_income)

        # Add new expenses
        new_expenses = pipeline_result.get("expenses", [])
        self.state["expenses"].extend(new_expenses)

        # Update tax analysis
        if pipeline_result.get("tax_analysis"):
            self.state["tax_analysis"] = pipeline_result["tax_analysis"]

        # Update insights
        if pipeline_result.get("insights"):
            self.state["insights"] = pipeline_result["insights"]

        # Log session
        self.state["session_count"] = self.state.get("session_count", 0) + 1
        self.state["agent_logs"].append({
            "session": self.state["session_count"],
            "time": datetime.now().isoformat(),
            "income_added": len(new_income),
            "expenses_added": len(new_expenses),
            "agents_used": pipeline_result.get("agents_used", []),
            "duration": pipeline_result.get("pipeline_duration", 0),
        })

        self.save()

    def clear(self):
        """Reset all state."""
        self.state = {
            "income": [],
            "expenses": [],
            "insights": [],
            "tax_analysis": {},
            "agent_logs": [],
            "session_count": 0,
        }
        self.save()
        print("[Memory] State cleared")

    def get_full_state(self) -> dict:
        """Return the full state for the frontend."""
        return self.state
