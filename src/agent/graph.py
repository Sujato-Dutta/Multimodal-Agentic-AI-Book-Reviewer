from langgraph.graph import StateGraph, END
from src.agent.state import BookReviewState
from src.agent.nodes.ocr_agent import vision_agent
from src.agent.nodes.verification import verification_agent
from src.agent.nodes.retrieval import retrieval_agent
from src.agent.nodes.rag import rag_agent
from src.agent.nodes.review import review_agent
from src.agent.nodes.recommendation import recommendation_agent
from src.agent.nodes.guardrail import guardrail_agent
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _should_continue_after_vision(state: BookReviewState) -> str:
    if state.get("error"):
        return "guardrail"
    if not state.get("detected_title"):
        return "guardrail"
    return "verification"


def build_graph() -> StateGraph:
    graph = StateGraph(BookReviewState)

    graph.add_node("vision", vision_agent)
    graph.add_node("verification", verification_agent)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("rag", rag_agent)
    graph.add_node("review", review_agent)
    graph.add_node("recommendation", recommendation_agent)
    graph.add_node("guardrail", guardrail_agent)

    graph.set_entry_point("vision")

    graph.add_conditional_edges(
        "vision",
        _should_continue_after_vision,
        {"verification": "verification", "guardrail": "guardrail"},
    )
    graph.add_edge("verification", "retrieval")
    graph.add_edge("retrieval", "rag")
    graph.add_edge("rag", "review")
    graph.add_edge("review", "recommendation")
    graph.add_edge("recommendation", "guardrail")
    graph.add_edge("guardrail", END)

    return graph.compile()


pipeline = build_graph()


async def analyze_book(image_bytes: bytes, filename: str) -> dict:
    logger.info(f"Starting book analysis pipeline for: {filename}")
    initial_state: BookReviewState = {
        "image_bytes": image_bytes,
        "filename": filename,
    }
    result = await pipeline.ainvoke(initial_state)
    return result.get("final_output", {})

