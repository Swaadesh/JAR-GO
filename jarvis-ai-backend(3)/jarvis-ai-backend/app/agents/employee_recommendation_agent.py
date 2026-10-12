"""
Employee Recommendation Agent (Day 4) -- REVISED.

No longer scores candidates itself. Narendra already built and owns
that logic (skill/role/capacity/history -> score + reason) at
POST /recommendations. This agent now: gets his ranked list, stages a
proposal for the top candidate, and turns his data into a
manager-facing explanation. The LLM adds value by explaining/phrasing,
not by deciding who's best -- that decision stays in one place.
"""
from app.llm import llm as _llm
from app.tools.proposal_tools import get_recommendations, stage_proposal


async def recommend_employee(task: str, top_n: int = 3) -> dict:
    """Get real recommendations for `task`, stage a proposal for the
    top candidate, and return an explanation plus the proposal id
    (needed later to approve/reject once the manager confirms)."""
    rec_response = await get_recommendations.ainvoke({"task": task, "top_n": top_n})
    ranked = rec_response if isinstance(rec_response, list) else rec_response.get("recommendations", rec_response)

    # TEMP DEBUG -- remove once the name/role mismatch is root-caused.
    import json
    print("=== DEBUG: raw ranked list from get_recommendations ===")
    print(json.dumps(ranked, indent=2, default=str))

    if not ranked:
        return {"error": "No candidates found for that task."}

    top = ranked[0]
    print(f"=== DEBUG: top candidate selected = {top} ===")

    proposal = await stage_proposal.ainvoke({
        "member": top["name"],
        "task": task,
        "reason": top.get("reason", ""),
    })
    print(f"=== DEBUG: stage_proposal called with member={top['name']!r} ===")
    print(f"=== DEBUG: stage_proposal response = {json.dumps(proposal, indent=2, default=str)} ===")

    reason = await _explain_recommendation(top, ranked[1:])

    return {
        "recommended_employee_name": top["name"],
        "score": top.get("score"),
        "reason": reason,
        "proposal_id": proposal.get("id"),
        "runner_ups": [r["name"] for r in ranked[1:]],
    }


async def _explain_recommendation(top: dict, runner_ups: list[dict]) -> str:
    prompt = (
        f"In 1-2 sentences, explain to a manager why {top['name']} is the best pick. "
        f"Their score breakdown: skill_match={top.get('skill_match')}, "
        f"role_match={top.get('role_match')}, capacity={top.get('capacity')}, "
        f"history={top.get('history')}. Existing system reason: \"{top.get('reason', '')}\". "
        "Be concrete, no fluff, and mention this needs the manager's confirmation before it's assigned."
    )
    response = await _llm.ainvoke(prompt)
    return response.content
