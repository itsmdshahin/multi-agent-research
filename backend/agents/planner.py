"""
Planner Agent — analyses the user query and produces an execution plan.
Determines which downstream agents to invoke and in what order.
"""
import json
from typing import Any, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.logging import get_logger

logger = get_logger(__name__)

PLANNER_SYSTEM_PROMPT = """You are the Planner Agent for an AI research assistant system.
Your job is to analyze a user's query and produce a JSON execution plan.

Available agents:
- retrieval: Search uploaded documents using semantic search
- web_search: Search the internet for current information
- research: Summarize, compare, and analyze documents
- coding: Generate or explain code
- citation: Track and format citations
- memory: Load relevant conversation history

Your plan must be a valid JSON object with this structure:
{
  "query_type": "research" | "coding" | "search" | "comparison" | "summary",
  "agents_to_use": ["memory", "retrieval", "research", "citation"],
  "sub_tasks": ["task1", "task2"],
  "needs_web_search": true | false,
  "complexity": "simple" | "medium" | "complex"
}

Rules:
- Always include "retrieval" and "citation" unless it's a pure coding question with no docs
- Include "web_search" only if the user explicitly wants current/online info
- Include "coding" if the query asks for code generation or debugging
- Include "memory" if the conversation has history or the query references prior context
- Keep sub_tasks concrete and actionable

Respond ONLY with valid JSON, no other text.
"""


class PlannerAgent:
    """
    Uses an LLM to determine the best execution plan for a given user query.
    Falls back to a safe default plan if LLM fails.
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    async def plan(
        self,
        query: str,
        document_ids: List[str],
        conversation_history: List[dict],
    ) -> dict:
        """Generate an execution plan for the given query."""
        context_summary = ""
        if conversation_history:
            context_summary = f"\n\nConversation has {len(conversation_history)} prior messages."

        if document_ids:
            context_summary += f"\n\n{len(document_ids)} documents are attached."

        user_message = f"Query: {query}{context_summary}"

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=user_message),
            ])

            plan_text = response.content.strip()
            # Strip markdown code fences if present
            if plan_text.startswith("```"):
                plan_text = plan_text.split("```")[1]
                if plan_text.startswith("json"):
                    plan_text = plan_text[4:]

            plan = json.loads(plan_text)
            logger.info("Plan generated", query_type=plan.get("query_type"), agents=plan.get("agents_to_use"))
            return plan

        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Planner LLM failed, using default plan", error=str(e))
            return self._default_plan(query)

    @staticmethod
    def _default_plan(query: str) -> dict:
        """Safe fallback plan when LLM planning fails."""
        query_lower = query.lower()
        is_coding = any(kw in query_lower for kw in ["code", "function", "implement", "debug", "python", "javascript"])
        needs_web = any(kw in query_lower for kw in ["latest", "current", "today", "recent", "news"])

        agents = ["retrieval", "research", "citation"]
        if is_coding:
            agents.append("coding")
        if needs_web:
            agents.append("web_search")

        return {
            "query_type": "coding" if is_coding else "research",
            "agents_to_use": agents,
            "sub_tasks": ["retrieve relevant context", "synthesize response"],
            "needs_web_search": needs_web,
            "complexity": "medium",
        }
