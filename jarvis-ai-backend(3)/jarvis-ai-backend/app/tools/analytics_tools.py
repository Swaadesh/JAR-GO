"""
Analytics tools.

The real backend has no /analytics/* endpoints and no project concept
at all -- everything is per-employee or per-task, team-wide. These
tools compute a summary from the real /employees and /tasks endpoints
instead of a fictional dedicated analytics endpoint.
"""
from langchain_core.tools import tool
from app.tools._client import backend_get


@tool
async def get_team_summary() -> dict:
    """Get an overall team snapshot: task counts by status, and each
    employee's live capacity/availability."""
    employees = await backend_get("/employees")
    open_tasks = await backend_get("/tasks", params={"status": "open"})
    completed_tasks = await backend_get("/tasks", params={"status": "completed"})
    return {
        "employee_count": len(employees),
        "open_task_count": len(open_tasks),
        "completed_task_count": len(completed_tasks),
        "employees": employees,
    }


@tool
async def get_employee_tasks_summary(member: str) -> dict:
    """Get one member's open and completed task counts."""
    open_tasks = await backend_get("/tasks", params={"member": member, "status": "open"})
    completed_tasks = await backend_get("/tasks", params={"member": member, "status": "completed"})
    return {"member": member, "open": len(open_tasks), "completed": len(completed_tasks)}


ANALYTICS_TOOLS = [get_team_summary, get_employee_tasks_summary]
