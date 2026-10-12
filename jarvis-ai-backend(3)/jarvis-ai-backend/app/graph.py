"""
Wires the Supervisor and specialist agents into the full LangGraph graph.

REVISED confirmation model (matches Narendra's real backend, not our
own invented rule anymore):
- create_task (direct allocation) has NO gate -- it's only ever called
  when a specific person is already named, which is Narendra's rule for
  skipping the gate entirely.
- The ONLY thing that needs manager confirmation is an AI-picked
  assignment, which goes through stage_proposal -> approve_proposal.
  That's why confirmation is checked BEFORE the normal intent routing:
  a bare "yes"/"confirm" with a pending proposal_id doesn't cleanly
  classify as any of the four intents, so it has to be handled first.

Caveat worth knowing: enforcement that "only a named-person request
uses create_task" lives in the Task Agent's prompt (it's told to refuse
to guess a name), not in server-side code -- Narendra's own API can't
tell the difference between "AI picked this" and "manager said this"
either. That's a property of his design, not something introduced here.
"""
from langgraph.graph import StateGraph, END
from app.state import JarvisState
from app.agents.supervisor import classify_intent
from app.agents.task_agent import task_agent
from app.agents.employee_recommendation_agent import recommend_employee
from app.agents.analytics_agent import analytics_agent
from app.agents.risk_agent import risk_agent
from app.tools.proposal_tools import approve_proposal, reject_proposal

_CONFIRM_WORDS = ["confirm", "yes", "approve", "go ahead", "do it"]
_DECLINE_WORDS = ["no", "cancel", "reject", "don't", "stop"]


def route_from_entry(state: JarvisState) -> str:
    text = state.get("input_text", "").lower()
    if state.get("proposal_id"):
        if state.get("confirmed") or any(w in text for w in _CONFIRM_WORDS):
            return "approve"
        if any(w in text for w in _DECLINE_WORDS):
            return "reject"
    return "supervisor"


async def approve_node(state: JarvisState) -> JarvisState:
    result = await approve_proposal.ainvoke({"proposal_id": state["proposal_id"]})
    return {"result": f"Approved and allocated: {result}", "requires_confirmation": False, "proposal_id": None}


async def reject_node(state: JarvisState) -> JarvisState:
    result = await reject_proposal.ainvoke({"proposal_id": state["proposal_id"]})
    return {"result": "Okay, discarded that proposal.", "requires_confirmation": False, "proposal_id": None}


async def supervisor_node(state: JarvisState) -> JarvisState:
    intent = await classify_intent(state["input_text"])
    return {"intent": intent}


def route_from_supervisor(state: JarvisState) -> str:
    return state.get("intent", "unknown")


def _build_context_suffix(state: JarvisState) -> str:
    bits = []
    if state.get("task_id"):
        bits.append(f"task_id={state['task_id']}")
    if state.get("employee_name"):
        bits.append(f"employee_name={state['employee_name']}")
    if not bits:
        return ""
    return f"\n\n(Known context -- use these directly, don't ask for them: {', '.join(bits)})"


async def task_node(state: JarvisState) -> JarvisState:
    augmented_text = state["input_text"] + _build_context_suffix(state)
    response = await task_agent.ainvoke({"messages": [{"role": "user", "content": augmented_text}]})
    final_message = response["messages"][-1].content
    return {"result": final_message}


async def employee_recommendation_node(state: JarvisState) -> JarvisState:
    rec = await recommend_employee(task=state["input_text"])
    if rec.get("error"):
        return {"result": rec["error"]}
    return {
        "result": rec.get("reason"),
        "recommended_employee_name": rec.get("recommended_employee_name"),
        "recommendation_reason": rec.get("reason"),
        "proposal_id": rec.get("proposal_id"),
        "requires_confirmation": True,
        "pending_action": "approve_proposal",
    }


async def analytics_node(state: JarvisState) -> JarvisState:
    response = await analytics_agent.ainvoke({"messages": [{"role": "user", "content": state["input_text"]}]})
    return {"result": response["messages"][-1].content}


async def risk_node(state: JarvisState) -> JarvisState:
    response = await risk_agent.ainvoke({"messages": [{"role": "user", "content": state["input_text"]}]})
    return {"result": response["messages"][-1].content}


async def unknown_node(state: JarvisState) -> JarvisState:
    return {"result": "I couldn't tell which kind of request that was. Try rephrasing?"}


def build_graph():
    graph = StateGraph(JarvisState)

    graph.add_node("route_entry", lambda state: {})  # no-op, just a routing point
    graph.add_node("approve", approve_node)
    graph.add_node("reject", reject_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("task", task_node)
    graph.add_node("employee_recommendation", employee_recommendation_node)
    graph.add_node("analytics", analytics_node)
    graph.add_node("risk", risk_node)
    graph.add_node("unknown", unknown_node)

    graph.set_entry_point("route_entry")
    graph.add_conditional_edges(
        "route_entry",
        route_from_entry,
        {"approve": "approve", "reject": "reject", "supervisor": "supervisor"},
    )
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "task": "task",
            "employee_recommendation": "employee_recommendation",
            "analytics": "analytics",
            "risk": "risk",
            "unknown": "unknown",
        },
    )
    graph.add_edge("approve", END)
    graph.add_edge("reject", END)
    graph.add_edge("task", END)
    graph.add_edge("employee_recommendation", END)
    graph.add_edge("analytics", END)
    graph.add_edge("risk", END)
    graph.add_edge("unknown", END)

    return graph.compile()


jarvis_graph = build_graph()
