"""
Task tools -- calls Narendra's real /api/v1/tasks endpoints directly.

Key differences from the old placeholder version:
- Task ids are integers, not strings like "task_1".
- There is NO separate "assign" endpoint. POST /tasks both creates AND
  assigns in one call, by naming the member directly. Per Narendra's
  rule: this path skips the manager-confirmation gate entirely, because
  the manager (or the calling agent) already named a specific person --
  the gate only applies when the AI itself picked who does the work
  (that flow lives in proposal_tools.py instead).
- There is no delete-task endpoint at all in the real backend. Only
  create, complete, and reassign exist.
"""
from langchain_core.tools import tool
from app.tools._client import backend_get, backend_post, backend_patch


@tool
async def list_tasks(member: str | None = None, status: str | None = None) -> dict:
    """List tasks, optionally filtered by member name and/or status
    ('open' or 'completed')."""
    params = {k: v for k, v in {"member": member, "status": status}.items() if v}
    return await backend_get("/tasks", params=params)


@tool
async def get_task(task_id: int) -> dict:
    """Get full details for a single task by its integer id."""
    return await backend_get(f"/tasks/{task_id}")


@tool
async def create_task(member: str, task: str, priority: str = "normal", due: str | None = None) -> dict:
    """Create AND assign a task in one step. Only call this when a
    SPECIFIC person's name (or role) is already known/named -- not for
    'assign it to the best available developer' style requests, which
    must go through get_recommendations + stage_proposal instead so a
    human approves who was picked."""
    payload = {"member": member, "task": task, "priority": priority, "due": due}
    return await backend_post("/tasks", payload)


@tool
async def complete_task(task_id: int) -> dict:
    """Mark a task as completed."""
    return await backend_patch(f"/tasks/{task_id}", {"action": "complete"})


@tool
async def reassign_task(task_id: int, to_member: str) -> dict:
    """Move an open task to a different member."""
    return await backend_patch(f"/tasks/{task_id}", {"action": "reassign", "to_member": to_member})


TASK_TOOLS = [list_tasks, get_task, create_task, complete_task, reassign_task]
