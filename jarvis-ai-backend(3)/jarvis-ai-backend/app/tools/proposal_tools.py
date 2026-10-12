"""
Recommendation + proposal/approval tools.

This replaces the old employee_recommendation_agent's own scoring
logic entirely. Narendra already built and owns this: recommendation
scoring (skill/role/capacity/history) AND the manager-approval gate
(propose -> approve/reject). Duplicating either here would give two
systems that could disagree -- so the AI layer now just calls his.

IMPORTANT (his rule, not ours): only ONE proposal can be pending
globally at a time (shared with his voice assistant too). Approve or
reject promptly after staging -- don't leave one sitting.
"""
from langchain_core.tools import tool
from app.tools._client import backend_get, backend_post


@tool
async def get_recommendations(task: str, top_n: int = 3) -> dict:
    """Get a ranked list of employees for a task description, with
    scores and a reason for each, from Narendra's real scoring engine.
    Read-only -- stages nothing."""
    return await backend_post("/recommendations", {"task": task, "top_n": top_n})


@tool
async def stage_proposal(member: str, task: str, priority: str = "normal", due: str | None = None, reason: str = "") -> dict:
    """Stage ONE assignment for manager approval. Use this (not
    create_task) whenever the AI -- not the manager -- picked who does
    the work. Nothing is allocated until stage_proposal_and_approve or
    approve_proposal is called."""
    items = [{"member": member, "task": task, "priority": priority, "due": due, "reason": reason}]
    return await backend_post("/proposals", {"items": items, "kind": "single"})


@tool
async def approve_proposal(proposal_id: int) -> dict:
    """Approve a pending proposal -- this is the actual moment the task
    gets allocated. Only call this after the manager has explicitly
    confirmed."""
    result = await backend_post(f"/proposals/{proposal_id}/approve", {})
    return {"allocated": result}


@tool
async def reject_proposal(proposal_id: int) -> dict:
    """Reject a pending proposal -- discards it, nothing gets allocated.
    Call this if the manager declines."""
    return await backend_post(f"/proposals/{proposal_id}/reject", {})


@tool
async def get_proposal(proposal_id: int) -> dict:
    """Look up a proposal's current status."""
    return await backend_get(f"/proposals/{proposal_id}")


PROPOSAL_TOOLS = [get_recommendations, stage_proposal, approve_proposal, reject_proposal, get_proposal]
