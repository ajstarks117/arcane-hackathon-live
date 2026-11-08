"""
ARCANE LangGraph Workflow — the central orchestration graph.

Nodes:
  VALIDATING   → runs the Validator Agent (Ajaya's sandbox)
  CREATING_PR  → calls Rishi's PR Agent to open a fix PR on GitHub

Edges:
  START → VALIDATING
  VALIDATING → (conditional)
      if tests_passed  → CREATING_PR
      if retry < 3     → VALIDATING   (retry)
      else             → ESCALATE     (log + end)
  CREATING_PR → END
"""

import logging
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from agents.validator_agent import run_validator
from agents.pr_agent import create_pr

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


# ── State schema ─────────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    # Incoming from webhook
    repo_full_name: str
    commit_sha: str
    failure_log: str

    # Set by AST / LLM layers (upstream of this graph)
    patch_diff: str
    failing_test: str

    # Set by Validator Agent
    tests_passed: bool
    retry_count: int
    validator_summary: str
    timeout: bool

    # Set by PR Agent
    pr_url: Optional[str]
    error: Optional[str]


# ── Node functions ───────────────────────────────────────────────────────────

def validating_node(state: AgentState) -> AgentState:
    """VALIDATING — delegates to Ajaya's Validator Agent."""
    logger.info("[LangGraph] Entering VALIDATING node")
    return run_validator(state)


def creating_pr_node(state: AgentState) -> AgentState:
    """CREATING_PR — delegates to Rishi's PR Agent."""
    logger.info("[LangGraph] Entering CREATING_PR node")
    try:
        pr_url = create_pr(
            repo_full_name=state["repo_full_name"],
            base_branch="main",
            commit_sha=state["commit_sha"],
            patch_diff=state.get("patch_diff", ""),
            failing_test=state.get("failing_test", "unknown"),
            validator_summary=state.get("validator_summary"),
        )
        logger.info(f"[LangGraph] PR created: {pr_url}")
        return {**state, "pr_url": pr_url}
    except Exception as e:
        logger.error(f"[LangGraph] PR creation failed: {e}")
        return {**state, "error": str(e)}


def escalate_node(state: AgentState) -> AgentState:
    """ESCALATE — retries exhausted or sandbox timed out."""
    logger.warning(
        f"[LangGraph] ESCALATING for commit {state.get('commit_sha', '?')[:7]}. "
        f"Retries: {state.get('retry_count', 0)}, "
        f"Timeout: {state.get('timeout', False)}"
    )
    return {**state, "error": "Max retries exceeded or sandbox timeout — escalated"}


# ── Conditional edge ─────────────────────────────────────────────────────────

def after_validation(state: AgentState) -> str:
    """Decide the next node after VALIDATING."""
    if state.get("tests_passed"):
        return "creating_pr"
    if state.get("retry_count", 0) >= MAX_RETRIES:
        logger.warning("[LangGraph] Retry cap (3) reached — escalating")
        return "escalate"
    logger.info(
        f"[LangGraph] Tests failed — retrying "
        f"({state.get('retry_count', 0)}/{MAX_RETRIES})"
    )
    return "validating"


# ── Build the graph ──────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("validating", validating_node)
    builder.add_node("creating_pr", creating_pr_node)
    builder.add_node("escalate", escalate_node)

    builder.set_entry_point("validating")

    builder.add_conditional_edges(
        "validating",
        after_validation,
        {
            "creating_pr": "creating_pr",
            "validating": "validating",
            "escalate": "escalate",
        },
    )

    builder.add_edge("creating_pr", END)
    builder.add_edge("escalate", END)

    return builder.compile()


# Pre-compiled graph instance — importable by the API consumer
graph = build_graph()
