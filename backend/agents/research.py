"""
Research Agent — synthesizes retrieved document chunks into coherent answers,
summaries, comparisons, and research reports.
"""
from typing import Any, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.logging import get_logger
from agents.retrieval import RetrievalAgent

logger = get_logger(__name__)

RESEARCH_SYSTEM_PROMPT = """You are an expert AI Research Assistant.

Your role:
- Synthesize information from multiple documents and web results
- Provide accurate, well-structured, comprehensive answers
- Compare and contrast information across sources
- Generate technical insights and research summaries
- Use markdown for formatting (headings, bullet points, tables, bold)
- Be thorough but concise
- Acknowledge if information is insufficient

When comparing papers or documents:
- Identify methodologies, findings, limitations
- Highlight similarities and differences clearly
- Use structured sections

IMPORTANT: Base your answer on the provided context. If the context doesn't contain the answer, say so clearly.
"""


class ResearchAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.retrieval_agent = RetrievalAgent(None)  # used for formatting

    async def analyze(
        self,
        query: str,
        chunks: List[dict],
        web_results: List[dict],
        conversation_history: List[dict],
        plan: Optional[dict] = None,
    ) -> str:
        """Generate a research answer from retrieved context."""
        query_type = (plan or {}).get("query_type", "research")

        # Build context from chunks
        context_parts = []
        if chunks:
            for chunk in chunks:
                doc = chunk.get("document_name", "Document")
                page = chunk.get("page_number", "?")
                text = chunk.get("text", "")
                score = chunk.get("score", 0.0)
                context_parts.append(f"[{doc}, Page {page}, Score: {score:.2f}]\n{text}")

        if web_results:
            context_parts.append("\n--- Web Search Results ---")
            for result in web_results:
                title = result.get("title", "Web Result")
                url = result.get("url", "")
                content = result.get("content", "")[:500]
                context_parts.append(f"[Web: {title}]\n{content}\nURL: {url}")

        context = "\n\n".join(context_parts) if context_parts else "No relevant documents found."

        # Build conversation history for LLM
        messages = [SystemMessage(content=RESEARCH_SYSTEM_PROMPT)]

        for msg in conversation_history[-6:]:  # last 3 exchanges
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=content))

        user_message = f"""Context from documents:
{context}

User Question: {query}

Please provide a comprehensive, well-structured answer based on the context above.
Use markdown formatting. Include specific references to documents/pages when relevant."""

        messages.append(HumanMessage(content=user_message))

        response = await self.llm.ainvoke(messages)
        return response.content

    async def generate_report(
        self,
        title: str,
        document_ids: List[str],
        prompt: Optional[str],
        chunks: List[dict],
        report_type: str = "research_summary",
    ) -> str:
        """Generate a structured research report from document chunks."""
        context = "\n\n".join([
            f"[{c.get('document_name')}, p.{c.get('page_number')}]\n{c.get('text')}"
            for c in chunks
        ])

        report_prompts = {
            "research_summary": "Create a comprehensive research summary with: Executive Summary, Key Findings, Methodology Analysis, Conclusions, and References.",
            "comparison": "Create a detailed comparison report with: Overview, Side-by-Side Comparison table, Similarities, Differences, Strengths/Weaknesses, and Recommendation.",
            "technical": "Create a technical deep-dive with: Introduction, Technical Details, Implementation Notes, Code Examples (if applicable), and Recommendations.",
        }

        prompt_instruction = prompt or report_prompts.get(report_type, report_prompts["research_summary"])

        messages = [
            SystemMessage(content="You are an expert technical writer and researcher. Generate professional, publication-quality reports in Markdown format."),
            HumanMessage(content=f"""Title: {title}

Document Context:
{context}

Instructions: {prompt_instruction}

Generate a comprehensive, well-structured report in Markdown format.""")
        ]

        response = await self.llm.ainvoke(messages)
        return response.content
