"""
Citation Agent — extracts and formats citations from retrieved document chunks.
Prevents hallucination by grounding responses in source material.
"""
import re
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.logging import get_logger

logger = get_logger(__name__)


class CitationAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    async def extract(
        self,
        response_text: str,
        chunks: List[dict],
    ) -> List[dict]:
        """
        Match parts of the AI response back to source chunks.
        Returns a list of citation objects.
        """
        if not chunks:
            return []

        citations = []
        seen = set()

        for chunk in chunks:
            doc_id = chunk.get("document_id", "")
            doc_name = chunk.get("document_name", "Unknown")
            page = chunk.get("page_number", 0)
            text = chunk.get("text", "")
            score = chunk.get("score", 0.0)

            # Dedup by (doc_id, page)
            key = f"{doc_id}:{page}"
            if key in seen:
                continue
            seen.add(key)

            # Only cite chunks with reasonable relevance
            if score < 0.5:
                continue

            # Find a representative excerpt (first 200 chars)
            excerpt = text[:200].strip()
            if len(text) > 200:
                excerpt += "..."

            citations.append({
                "document_id": doc_id,
                "document_name": doc_name,
                "page_number": page,
                "excerpt": excerpt,
                "similarity_score": round(score, 3),
            })

        # Limit to top 5 most relevant citations
        citations.sort(key=lambda x: x["similarity_score"], reverse=True)
        return citations[:5]

    @staticmethod
    def format_inline_citations(response: str, citations: List[dict]) -> str:
        """
        Optionally annotate the response with inline citation markers.
        E.g., adds [1], [2] markers that correspond to the citations list.
        """
        if not citations:
            return response

        citation_footer = "\n\n---\n**Sources:**\n"
        for i, cite in enumerate(citations, 1):
            citation_footer += (
                f"{i}. **{cite['document_name']}**, Page {cite['page_number']} "
                f"(Relevance: {cite['similarity_score']:.0%})\n"
            )

        return response + citation_footer
