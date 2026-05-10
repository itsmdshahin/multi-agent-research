"""
LangGraph Multi-Agent Orchestration Workflow.

Graph structure:
  User Query → Planner → [Retrieval, WebSearch, Research, Coding, Citation, Memory]
             → Synthesizer → Response

Each node is an agent that processes state and passes it forward.
"""
import json
import uuid
from typing import Annotated, Any, AsyncIterator, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from core.config import settings
from core.logging import get_logger
from agents.planner import PlannerAgent
from agents.retrieval import RetrievalAgent
from agents.research import ResearchAgent
from agents.coding import CodingAgent
from agents.citation import CitationAgent
from agents.web_search import WebSearchAgent
from agents.memory import MemoryAgent

logger = get_logger(__name__)


# ─────────────────────────── State Definition ────────────────────────────

class AgentState(TypedDict):
    """Shared state passed between all agents in the graph."""
    # Input
    user_query: str
    conversation_id: str
    user_id: str
    document_ids: List[str]
    enable_web_search: bool
    conversation_history: List[dict]  # [{role, content}]

    # Planning
    plan: Optional[dict]  # planner output: {agents_to_use, sub_tasks, query_type}

    # Retrieved context
    retrieved_chunks: List[dict]  # from Qdrant
    web_search_results: List[dict]

    # Agent outputs
    research_summary: Optional[str]
    code_snippets: Optional[List[dict]]
    citations: List[dict]

    # Final
    final_response: Optional[str]
    agent_activity: List[dict]  # [{agent, action, status, detail}]
    error: Optional[str]

    # Injected services (not serialized — set at runtime)
    _vector_store: Any
    _memory_cache: Any
    _model: str


# ─────────────────────────── Workflow Builder ────────────────────────────

class MultiAgentWorkflow:
    """
    LangGraph workflow that orchestrates all research agents.
    Supports both full execution and streaming via async generators.
    """

    def __init__(self, vector_store, memory_cache, model: str = None):
        self.vector_store = vector_store
        self.memory_cache = memory_cache
        self.model = model or settings.OPENAI_MODEL

        self.llm = ChatOpenAI(
            model=self.model,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            streaming=True,
        )

        # Agent instances
        self.planner = PlannerAgent(self.llm)
        self.retrieval = RetrievalAgent(self.vector_store)
        self.research = ResearchAgent(self.llm)
        self.coding = CodingAgent(self.llm)
        self.citation = CitationAgent(self.llm)
        self.web_search = WebSearchAgent()
        self.memory_agent = MemoryAgent(self.memory_cache)

        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Construct the LangGraph state machine."""
        builder = StateGraph(AgentState)

        # Register nodes
        builder.add_node("planner", self._planner_node)
        builder.add_node("memory", self._memory_node)
        builder.add_node("retrieval", self._retrieval_node)
        builder.add_node("web_search", self._web_search_node)
        builder.add_node("research", self._research_node)
        builder.add_node("coding", self._coding_node)
        builder.add_node("citation", self._citation_node)
        builder.add_node("synthesizer", self._synthesizer_node)

        # Entry point
        builder.set_entry_point("planner")

        # Planner → conditional routing
        builder.add_conditional_edges("planner", self._route_after_planner)

        # Memory always runs after planner
        builder.add_edge("memory", "retrieval")

        # Retrieval → conditional
        builder.add_conditional_edges("retrieval", self._route_after_retrieval)

        # Web search → research
        builder.add_edge("web_search", "research")

        # Research → coding (if needed) or citation
        builder.add_conditional_edges("research", self._route_after_research)

        # Coding → citation
        builder.add_edge("coding", "citation")

        # Citation → synthesizer
        builder.add_edge("citation", "synthesizer")

        # Synthesizer → END
        builder.add_edge("synthesizer", END)

        return builder.compile()

    # ─────────────────────────── Routing Functions ────────────────────────────

    def _route_after_planner(self, state: AgentState) -> str:
        """Decide whether to load memory or jump straight to retrieval."""
        plan = state.get("plan", {}) or {}
        agents = plan.get("agents_to_use", [])

        if "memory" in agents:
            return "memory"
        return "retrieval"

    def _route_after_retrieval(self, state: AgentState) -> str:
        plan = state.get("plan", {}) or {}
        agents = plan.get("agents_to_use", [])

        if state.get("enable_web_search") or "web_search" in agents:
            return "web_search"
        return "research"

    def _route_after_research(self, state: AgentState) -> str:
        plan = state.get("plan", {}) or {}
        query_type = plan.get("query_type", "research")

        if query_type == "coding":
            return "coding"
        return "citation"

    # ─────────────────────────── Agent Nodes ────────────────────────────

    async def _planner_node(self, state: AgentState) -> dict:
        self._log_activity(state, "planner", "Planning agent workflow...")
        try:
            plan = await self.planner.plan(
                query=state["user_query"],
                document_ids=state.get("document_ids", []),
                conversation_history=state.get("conversation_history", []),
            )
            self._log_activity(state, "planner", "Plan created", "done",
                               f"Agents: {', '.join(plan.get('agents_to_use', []))}")
            return {"plan": plan}
        except Exception as e:
            logger.error("Planner failed", error=str(e))
            return {
                "plan": {"agents_to_use": ["retrieval", "research", "citation"], "query_type": "research"},
                "error": str(e),
            }

    async def _memory_node(self, state: AgentState) -> dict:
        self._log_activity(state, "memory", "Loading conversation memory...")
        try:
            history = await self.memory_agent.get_relevant_history(
                conversation_id=state["conversation_id"],
                current_query=state["user_query"],
            )
            self._log_activity(state, "memory", "Memory loaded", "done",
                               f"{len(history)} messages retrieved")
            return {"conversation_history": history}
        except Exception as e:
            logger.warning("Memory agent failed", error=str(e))
            return {}

    async def _retrieval_node(self, state: AgentState) -> dict:
        self._log_activity(state, "retrieval", "Searching documents...")
        try:
            chunks = await self.retrieval.retrieve(
                query=state["user_query"],
                document_ids=[str(did) for did in state.get("document_ids", [])],
                user_id=state["user_id"],
                top_k=settings.TOP_K_RETRIEVAL,
                score_threshold=settings.SIMILARITY_THRESHOLD,
            )
            self._log_activity(state, "retrieval", "Document search complete", "done",
                               f"{len(chunks)} chunks found")
            return {"retrieved_chunks": chunks}
        except Exception as e:
            logger.error("Retrieval failed", error=str(e))
            return {"retrieved_chunks": [], "error": str(e)}

    async def _web_search_node(self, state: AgentState) -> dict:
        self._log_activity(state, "web_search", "Searching the web...")
        try:
            results = await self.web_search.search(
                query=state["user_query"],
                num_results=5,
            )
            self._log_activity(state, "web_search", "Web search complete", "done",
                               f"{len(results)} results found")
            return {"web_search_results": results}
        except Exception as e:
            logger.warning("Web search failed", error=str(e))
            return {"web_search_results": []}

    async def _research_node(self, state: AgentState) -> dict:
        self._log_activity(state, "research", "Analyzing documents...")
        try:
            summary = await self.research.analyze(
                query=state["user_query"],
                chunks=state.get("retrieved_chunks", []),
                web_results=state.get("web_search_results", []),
                conversation_history=state.get("conversation_history", []),
                plan=state.get("plan", {}),
            )
            self._log_activity(state, "research", "Analysis complete", "done")
            return {"research_summary": summary}
        except Exception as e:
            logger.error("Research agent failed", error=str(e))
            return {"research_summary": "", "error": str(e)}

    async def _coding_node(self, state: AgentState) -> dict:
        self._log_activity(state, "coding", "Generating code...")
        try:
            snippets = await self.coding.generate(
                query=state["user_query"],
                context=state.get("research_summary", ""),
                chunks=state.get("retrieved_chunks", []),
            )
            self._log_activity(state, "coding", "Code generation complete", "done")
            return {"code_snippets": snippets}
        except Exception as e:
            logger.error("Coding agent failed", error=str(e))
            return {"code_snippets": []}

    async def _citation_node(self, state: AgentState) -> dict:
        self._log_activity(state, "citation", "Generating citations...")
        try:
            citations = await self.citation.extract(
                response_text=state.get("research_summary", ""),
                chunks=state.get("retrieved_chunks", []),
            )
            self._log_activity(state, "citation", "Citations ready", "done",
                               f"{len(citations)} citations")
            return {"citations": citations}
        except Exception as e:
            logger.warning("Citation agent failed", error=str(e))
            return {"citations": []}

    async def _synthesizer_node(self, state: AgentState) -> dict:
        """Combine all agent outputs into a final coherent response."""
        self._log_activity(state, "synthesizer", "Composing final response...")

        parts: List[str] = []

        if state.get("research_summary"):
            parts.append(state["research_summary"])

        if state.get("code_snippets"):
            for snippet in state["code_snippets"]:
                lang = snippet.get("language", "python")
                code = snippet.get("code", "")
                parts.append(f"\n```{lang}\n{code}\n```")

        final_response = "\n\n".join(parts) if parts else "I could not find relevant information to answer your question."

        # Save to memory
        try:
            await self.memory_agent.save_exchange(
                conversation_id=state["conversation_id"],
                user_message=state["user_query"],
                assistant_message=final_response,
            )
        except Exception as e:
            logger.warning("Failed to save to memory", error=str(e))

        self._log_activity(state, "synthesizer", "Response ready", "done")
        return {"final_response": final_response}

    # ─────────────────────────── Helpers ────────────────────────────

    @staticmethod
    def _log_activity(state: AgentState, agent: str, action: str, status: str = "running", detail: str = None) -> None:
        """Append an activity entry to state's agent_activity list."""
        activity = state.setdefault("agent_activity", [])
        activity.append({"agent": agent, "action": action, "status": status, "detail": detail})

    async def execute(self, initial_state: dict) -> AgentState:
        """Run the full workflow and return the final state."""
        # Inject services
        initial_state["_vector_store"] = self.vector_store
        initial_state["_memory_cache"] = self.memory_cache
        initial_state.setdefault("agent_activity", [])
        initial_state.setdefault("citations", [])
        initial_state.setdefault("web_search_results", [])
        initial_state.setdefault("retrieved_chunks", [])

        final_state = await self.graph.ainvoke(initial_state)
        return final_state

    async def stream_execute(self, initial_state: dict) -> AsyncIterator[dict]:
        """
        Execute the workflow and yield SSE-compatible event dicts as each
        agent completes or each token is produced.
        """
        initial_state["_vector_store"] = self.vector_store
        initial_state["_memory_cache"] = self.memory_cache
        initial_state.setdefault("agent_activity", [])
        initial_state.setdefault("citations", [])
        initial_state.setdefault("web_search_results", [])
        initial_state.setdefault("retrieved_chunks", [])

        seen_activities: set = set()

        async for event in self.graph.astream(initial_state, stream_mode="values"):
            # Emit any new agent activities
            for activity in event.get("agent_activity", []):
                key = f"{activity['agent']}:{activity['action']}:{activity['status']}"
                if key not in seen_activities:
                    seen_activities.add(key)
                    yield {
                        "event_type": "agent_activity",
                        "data": activity,
                    }

            # Emit citations when available
            if event.get("citations"):
                yield {
                    "event_type": "citations",
                    "data": event["citations"],
                }

            # Emit final response
            if event.get("final_response") and event.get("final_response") != initial_state.get("final_response"):
                yield {
                    "event_type": "response",
                    "content": event["final_response"],
                }

        yield {"event_type": "done", "data": None}
