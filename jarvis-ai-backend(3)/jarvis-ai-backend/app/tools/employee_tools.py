"""
Employee tools -- calls Narendra's real /api/v1/employees endpoints.

Key differences from the old placeholder version:
- Employees are identified by NAME (string), not an id.
- Workload/availability come back INLINE on every employee record
  (open, overdue, high_priority, capacity_pct, capacity_label,
  available) -- computed live on his side. No separate workload or
  availability calls needed anymore.
- There is NO performance field anywhere in the real system (no
  rating/completion-rate/review data exists). Do not reference it.
"""
from langchain_core.tools import tool
from app.tools._client import backend_get


@tool
async def list_employees() -> dict:
    """List every employee, each with live workload/availability fields
    merged in (open, overdue, high_priority, capacity_pct,
    capacity_label, available). No skill filter is supported server-side
    -- filter the returned list client-side if needed."""
    result = await backend_get("/employees")
    return {"employees": result}


@tool
async def get_employee(name: str) -> dict:
    """Get one employee by name (case-insensitive; role also matches,
    e.g. 'backend developer')."""
    return await backend_get(f"/employees/{name}")


EMPLOYEE_TOOLS = [list_employees, get_employee]
