"""
FastAPI integration for the AI layer (Day 6).

This can run as its own microservice, or Narendra can mount this
router inside his main FastAPI app -- either works. Keeping it
separate here so the AI layer stays independently testable.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.graph import jarvis_graph
from app.state import JarvisState

app = FastAPI(title="JARVIS AI Layer")


class CommandRequest(BaseModel):
    text: str
    task_id: int | None = None
    employee_name: str | None = None
    proposal_id: int | None = None
    confirmed: bool = False


class CommandResponse(BaseModel):
    result: str | None
    requires_confirmation: bool = False
    pending_action: str | None = None
    proposal_id: int | None = None
    recommended_employee_name: str | None = None
    recommendation_reason: str | None = None


@app.post("/api/ai/command", response_model=CommandResponse)
async def run_command(req: CommandRequest):
    """Single entry point for both typed commands and transcribed voice
    commands. IMPORTANT: after a recommendation response comes back
    with requires_confirmation=True and a proposal_id, the frontend
    MUST send that same proposal_id back on the manager's next message
    (e.g. "yes") -- that's how the graph knows what's being confirmed."""
    initial_state: JarvisState = {
        "input_text": req.text,
        "task_id": req.task_id,
        "employee_name": req.employee_name,
        "proposal_id": req.proposal_id,
        "confirmed": req.confirmed,
    }
    try:
        final_state = await jarvis_graph.ainvoke(initial_state)
    except Exception as exc:  # noqa: BLE001 -- surfaced to caller, not swallowed
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return CommandResponse(
        result=final_state.get("result"),
        requires_confirmation=final_state.get("requires_confirmation", False),
        pending_action=final_state.get("pending_action"),
        proposal_id=final_state.get("proposal_id"),
        recommended_employee_name=final_state.get("recommended_employee_name"),
        recommendation_reason=final_state.get("recommendation_reason"),
    )


@app.get("/api/ai/health")
async def health():
    return {"status": "ok"}
