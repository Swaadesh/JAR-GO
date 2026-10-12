"""
Supervisor Agent (Day 2, extended through Day 5 for voice).

Classifies the manager's command into one of the four specialist lanes.
Keyword routing first (cheap, deterministic, good for the voice-command
demo scenarios) with an LLM fallback for anything ambiguous.
"""
from app.llm import llm as _llm
from app.state import IntentType

# Checked FIRST, before anything else. "assign the task to the best
# available developer" contains both an explicit action verb ("assign")
# and a recommendation-sounding phrase ("best available") -- an action
# verb always wins, because the manager is telling JARVIS to DO
# something, not just asking who's best. Without this, that command
# would wrongly match "employee_recommendation" on "best available" and
# never reach the Task Agent (or the confirmation gate) at all.
_ACTION_KEYWORDS = ["assign", "delete", "remove", "create task", "add task", "update task"]

_KEYWORDS: dict[IntentType, list[str]] = {
    "employee_recommendation": ["recommend", "who should", "who can take", "which employee"],
    "task": ["pending tasks", "list tasks", "show tasks"],
    "analytics": ["report", "progress", "dashboard", "summary", "how many tasks", "completion"],
    "risk": ["overdue", "at risk", "stalled", "overloaded", "behind schedule", "risk"],
}


async def classify_intent(text: str) -> IntentType:
    lowered = text.lower()

    if any(p in lowered for p in _ACTION_KEYWORDS):
        return "task"

    for intent, phrases in _KEYWORDS.items():
        if any(p in lowered for p in phrases):
            return intent

    # Fallback: let the LLM decide among the four lanes
    prompt = (
        "Classify this manager command into exactly one label: "
        "task, employee_recommendation, analytics, or risk. "
        f'Command: "{text}"\n'
        "Reply with only the label, nothing else."
    )
    response = await _llm.ainvoke(prompt)
    label = response.content.strip().lower()
    if label in ("task", "employee_recommendation", "analytics", "risk"):
        return label  # type: ignore[return-value]
    return "unknown"

