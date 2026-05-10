"""
Coding Agent — generates, explains, and debugs code from document context.
Supports Python, JavaScript, TypeScript, and other languages.
"""
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.logging import get_logger

logger = get_logger(__name__)

CODING_SYSTEM_PROMPT = """You are an expert software engineer and coding assistant.

Your capabilities:
- Generate production-quality code from specifications or document context
- Explain code snippets clearly
- Debug and fix code issues
- Generate APIs, functions, classes, and scripts
- Support Python, JavaScript, TypeScript, SQL, Bash, and more

Code quality standards:
- Add meaningful comments
- Use type hints (Python) or TypeScript types
- Follow SOLID principles
- Handle errors properly
- Write clean, readable code

Format: Return code inside proper markdown code blocks with language tags.
"""


class CodingAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    async def generate(
        self,
        query: str,
        context: str,
        chunks: List[dict],
    ) -> List[dict]:
        """Generate code snippets based on the user query and document context."""
        # Extract relevant context
        doc_context = "\n\n".join([
            f"[{c.get('document_name')}, p.{c.get('page_number')}]\n{c.get('text', '')}"
            for c in chunks[:3]  # Use top 3 chunks for coding context
        ])

        combined_context = ""
        if doc_context:
            combined_context += f"Document Context:\n{doc_context}\n\n"
        if context:
            combined_context += f"Research Summary:\n{context}"

        messages = [
            SystemMessage(content=CODING_SYSTEM_PROMPT),
            HumanMessage(content=f"""{combined_context}

Coding Request: {query}

Generate high-quality, production-ready code. Include:
1. The main implementation
2. Usage examples
3. Brief explanation""")
        ]

        response = await self.llm.ainvoke(messages)
        content = response.content

        # Parse code blocks from the response
        snippets = self._extract_code_blocks(content)
        if not snippets:
            # Return the full response as a single snippet
            snippets = [{"language": "text", "code": content, "description": "Generated code"}]

        return snippets

    @staticmethod
    def _extract_code_blocks(text: str) -> List[dict]:
        """Extract language-tagged code blocks from markdown."""
        import re
        snippets = []
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)

        for lang, code in matches:
            snippets.append({
                "language": lang or "text",
                "code": code.strip(),
                "description": "",
            })

        return snippets
