"""
Risk tools.

Narendra's employee records already compute "overdue" and
"capacity_label" (High/Medium/Low/Overloaded) live -- no separate risk
endpoint exists or is needed. These tools just surface the employees
that need attention from that same data, so the Risk Agent isn't
re-deriving numbers Narendra's side already computed.
"""
from langchain_core.tools import tool
from app.tools._client import backend_get


@tool
async def get_overloaded_employees() -> dict:
    """Get employees whose capacity_label is 'Overloaded' (per
    Narendra's live workload calculation)."""
    employees = await backend_get("/employees")
    overloaded = [e for e in employees if e.get("capacity_label") == "Overloaded"]
    return {"overloaded": overloaded}


@tool
async def get_employees_with_overdue_tasks() -> dict:
    """Get employees who currently have at least one overdue task."""
    employees = await backend_get("/employees")
    with_overdue = [e for e in employees if e.get("overdue", 0) > 0]
    return {"employees_with_overdue": with_overdue}


RISK_TOOLS = [get_overloaded_employees, get_employees_with_overdue_tasks]
