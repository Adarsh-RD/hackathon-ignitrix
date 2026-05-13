"""
returnX AI — Base Agent (LangChain)
Abstract base class using LangChain's ChatGroq.
Each agent follows the ReAct (Reason + Act) pattern.
"""

import json
import time
from abc import ABC, abstractmethod
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage


class BaseAgent(ABC):
    """Abstract base agent with ReAct loop using LangChain."""

    def __init__(self, name: str, role: str, llm: ChatGroq = None):
        self.name = name
        self.role = role
        self.llm = llm
        self.execution_log = []

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def run(self, input_data: dict) -> dict:
        pass

    def think(self, observation: str) -> str:
        """ReAct: Thought step."""
        entry = {"type": "thought", "content": observation, "time": time.time()}
        self.execution_log.append(entry)
        print(f"  [{self.name}] THOUGHT: {observation}")
        return observation

    def act(self, action: str, tool_name: str = None) -> str:
        """ReAct: Action step."""
        entry = {"type": "action", "tool": tool_name, "content": action, "time": time.time()}
        self.execution_log.append(entry)
        print(f"  [{self.name}] ACTION: {action}" + (f" (tool: {tool_name})" if tool_name else ""))
        return action

    def observe(self, result: str) -> str:
        """ReAct: Observation step."""
        entry = {"type": "observation", "content": result, "time": time.time()}
        self.execution_log.append(entry)
        print(f"  [{self.name}] OBSERVE: {result[:100]}...")
        return result

    def call_llm(self, user_message: str, json_mode: bool = True) -> dict | str:
        """Call LLM via LangChain ChatGroq."""
        if not self.llm:
            raise RuntimeError(f"[{self.name}] No LLM configured")

        self.act(f"Calling LangChain ChatGroq with {len(user_message)} chars", tool_name="langchain_llm")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=user_message),
        ]

        if json_mode:
            response = self.llm.invoke(
                messages,
                response_format={"type": "json_object"},
            )
        else:
            response = self.llm.invoke(messages)

        raw = response.content

        if json_mode:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                import re
                match = re.search(r"\{[\s\S]*\}", raw)
                parsed = json.loads(match.group()) if match else {}
            self.observe(f"Parsed JSON with {len(parsed)} keys")
            return parsed

        self.observe(f"Got text response: {len(raw)} chars")
        return raw

    def get_log(self) -> list:
        return self.execution_log
