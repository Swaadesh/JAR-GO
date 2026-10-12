"""
Mock stand-in for Narendra's REAL API contract (as of his spec message).

Mirrors: /api/v1 prefix, X-API-Key auth, employees by name with live
workload merged in, tasks by integer id, recommendations (read-only),
proposals (single global pending slot, propose -> approve/reject).

Run: uvicorn mock_backend.main:app --port 9000
Then: BACKEND_BASE_URL=http://localhost:9000/api/v1
"""
from fastapi import FastAPI, HTTPException, Header
from datetime import datetime, timezone

app = FastAPI(title="Mock Narendra Backend (real contract)")

FAKE_KEY = "test-key"


def _check_key(x_api_key: str | None):
    if x_api_key != FAKE_KEY:
        raise HTTPException(401, "invalid or missing X-API-Key")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- data

MEMBERS = [
    {"name": "Priya", "role": "backend developer", "phone": "", "skills": ["python", "fastapi", "auth", "api"]},
    {"name": "Ravi", "role": "backend developer", "phone": "", "skills": ["python", "api", "database", "fastapi"]},
    {"name": "Anjali", "role": "QA", "phone": "", "skills": ["testing", "qa", "automation"]},
]

TASKS: list[dict] = [
    {
        "id": 1, "member": "Ravi", "role": "backend developer", "task": "fix the login bug",
        "priority": "high", "due": "Friday", "status": "open", "created": _now(), "completed": None,
    },
]

PROPOSALS: list[dict] = []
_pending_proposal: dict | None = None


def _employee_with_workload(m: dict) -> dict:
    open_tasks = [t for t in TASKS if t["member"] == m["name"] and t["status"] == "open"]
    overdue = 0  # mock: no real date parsing, keep simple
    open_count = len(open_tasks)
    capacity_pct = min(int(open_count / 5 * 100), 100)
    capacity_label = "Overloaded" if open_count >= 5 else "High" if open_count >= 3 else "Medium" if open_count >= 1 else "Low"
    available = "No" if open_count >= 5 else "Limited" if open_count >= 3 else "Yes"
    return {
        **m,
        "open": open_count,
        "overdue": overdue,
        "high_priority": len([t for t in open_tasks if t["priority"] == "high"]),
        "capacity_pct": capacity_pct,
        "capacity_label": capacity_label,
        "available": available,
    }


# ------------------------------------------------------------- employees

@app.get("/api/v1/employees")
def list_employees(x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    return [_employee_with_workload(m) for m in MEMBERS]


@app.get("/api/v1/employees/{name}")
def get_employee(name: str, x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    for m in MEMBERS:
        if m["name"].lower() == name.lower() or m["role"].lower() == name.lower():
            return _employee_with_workload(m)
    raise HTTPException(404, "not found")


# ------------------------------------------------------------------ tasks

@app.get("/api/v1/tasks")
def list_tasks(member: str | None = None, status: str | None = None, x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    results = TASKS
    if member:
        results = [t for t in results if t["member"].lower() == member.lower()]
    if status:
        results = [t for t in results if t["status"] == status]
    return results


@app.get("/api/v1/tasks/{task_id}")
def get_task(task_id: int, x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    for t in TASKS:
        if t["id"] == task_id:
            return t
    raise HTTPException(404, "not found")


def _resolve_member(name_or_role: str) -> dict:
    for m in MEMBERS:
        if m["name"].lower() == name_or_role.lower() or m["role"].lower() == name_or_role.lower():
            return m
    raise HTTPException(400, f"'{name_or_role}' is not on the team")


@app.post("/api/v1/tasks", status_code=201)
def create_task(payload: dict, x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    who = _resolve_member(payload["member"])
    record = {
        "id": max((t["id"] for t in TASKS), default=0) + 1,
        "member": who["name"],
        "role": who["role"],
        "task": payload["task"],
        "priority": payload.get("priority") or "normal",
        "due": payload.get("due"),
        "status": "open",
        "created": _now(),
        "completed": None,
    }
    TASKS.append(record)
    return record


@app.patch("/api/v1/tasks/{task_id}")
def update_task(task_id: int, payload: dict, x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    task = next((t for t in TASKS if t["id"] == task_id), None)
    if not task:
        raise HTTPException(404, "not found")
    if payload.get("action") == "complete":
        task["status"] = "completed"
        task["completed"] = _now()
    elif payload.get("action") == "reassign":
        who = _resolve_member(payload["to_member"])
        task["member"] = who["name"]
        task["role"] = who["role"]
    return task


# --------------------------------------------------- recommendations/proposals

@app.post("/api/v1/recommendations")
def recommend(payload: dict, x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    task_text = payload.get("task", "").lower()
    top_n = payload.get("top_n", 3)

    scored = []
    for m in MEMBERS:
        emp = _employee_with_workload(m)
        skill_hits = sum(1 for s in m["skills"] if s in task_text)
        skill_match = min(skill_hits / 3, 1.0) if skill_hits else 0.2
        capacity = max(0.0, 1.0 - emp["open"] / 5)
        score = round((skill_match * 0.5 + capacity * 0.5) * 100)
        scored.append({
            "name": m["name"], "role": m["role"], "score": score,
            "skill_match": skill_match, "role_match": True, "capacity": capacity,
            "capacity_pct": emp["capacity_pct"], "history": 0.5,
            "reason": f"{m['name']} has {'a strong' if skill_match > 0.5 else 'some'} skill match and {emp['capacity_label'].lower()} capacity.",
        })
    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored[:top_n]


@app.post("/api/v1/proposals", status_code=201)
def stage_proposal(payload: dict, x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    global _pending_proposal
    if _pending_proposal is not None:
        for p in PROPOSALS:
            if p["id"] == _pending_proposal["id"]:
                p["status"] = "superseded"
    items = []
    for item in payload["items"]:
        who = _resolve_member(item["member"])
        items.append({
            "member": who["name"], "role": who["role"], "task": item["task"],
            "priority": item.get("priority") or "normal", "due": item.get("due"),
            "reason": item.get("reason", ""),
        })
    proposal = {
        "id": max((p["id"] for p in PROPOSALS), default=0) + 1,
        "kind": payload.get("kind", "single"),
        "items": items,
        "status": "pending",
        "created": _now(),
        "resolved": None,
    }
    PROPOSALS.append(proposal)
    _pending_proposal = proposal
    return proposal


@app.get("/api/v1/proposals")
def list_proposals(x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    return PROPOSALS


@app.get("/api/v1/proposals/{proposal_id}")
def get_proposal(proposal_id: int, x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    for p in PROPOSALS:
        if p["id"] == proposal_id:
            return p
    raise HTTPException(404, "not found")


@app.post("/api/v1/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: int, x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    global _pending_proposal
    if _pending_proposal is None or _pending_proposal["id"] != proposal_id:
        raise HTTPException(409, "not the currently pending proposal")
    proposal = _pending_proposal
    _pending_proposal = None
    records = []
    for item in proposal["items"]:
        record = create_task({"member": item["member"], "task": item["task"],
                               "priority": item["priority"], "due": item["due"]}, x_api_key=x_api_key)
        record["proposed_by"] = "ai"
        record["approved"] = _now()
        records.append(record)
    for p in PROPOSALS:
        if p["id"] == proposal_id:
            p["status"] = "approved"
            p["resolved"] = _now()
    return records


@app.post("/api/v1/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: int, x_api_key: str | None = Header(None)):
    _check_key(x_api_key)
    global _pending_proposal
    if _pending_proposal is None or _pending_proposal["id"] != proposal_id:
        raise HTTPException(409, "not the currently pending proposal")
    proposal = _pending_proposal
    _pending_proposal = None
    for p in PROPOSALS:
        if p["id"] == proposal_id:
            p["status"] = "rejected"
            p["resolved"] = _now()
    return proposal
