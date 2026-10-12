"""
Shared state that flows through the LangGraph.

This is the one object every agent reads from and writes to. Keeping it
in one place makes it easy for Khushi/Narendra to see exactly what shape
of data the AI layer expects and returns.
"""
from typing import Annotated, Any, Literal, Optional, TypedDict
from langgraph.graph.message import add_messages


IntentType = Literal[
    "task",
    "employee_recommendation",
    "analytics",
    "risk",
    "unknown",
]


class JarvisState(TypedDict, total=False):
    # Conversation / command history (LangGraph appends automatically)
    messages: Annotated[list, add_messages]

    # Raw input from the manager (typed or transcribed from voice)
    input_text: str

    # Which specialist agent the Supervisor routed to
    intent: IntentType

    # Context the frontend already knows (e.g. from the current screen).
    # NOTE: real backend identifies employees by NAME and tasks by
    # INTEGER id -- no project concept exists at all.
    task_id: Optional[int]
    employee_name: Optional[str]

    # Populated by the Employee Recommendation Agent -- proposal_id is
    # required to approve/reject once the manager confirms, since
    # Narendra's system stages AI-picked assignments rather than
    # allocating them immediately.
    recommended_employee_name: Optional[str]
    recommendation_reason: Optional[str]
    proposal_id: Optional[int]

    # Populated by any agent that produces a final answer
    result: Optional[Any]

    # Confirmation gate -- ONLY applies to AI-picked assignments (i.e. a
    # pending proposal). Direct allocation, where the manager already
    # named a specific person, never sets this.
    pending_action: Optional[str]
    requires_confirmation: bool
    confirmed: bool

    # Set if something goes wrong so the Supervisor can respond gracefully
    error: Optional[str]
