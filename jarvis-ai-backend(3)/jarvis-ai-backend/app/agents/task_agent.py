"""
Task Agent (Day 3) -- REVISED to match the real backend contract.

Real rules from Narendra's system (not ours to override):
- create_task both creates AND assigns in one call, immediately, no
  gate -- but ONLY when a specific person is already named. If the
  manager wants "the best available developer" or similar, this agent
  must NOT guess a name -- that has to go through the Employee
  Recommendation Agent's proposal flow instead (handled one level up,
  in graph.py).
- There is no delete-task capability in the real backend at all --
  only create, complete, and reassign exist. Say so if asked to delete.
- Tasks are identified by integer id; employees by name.
"""
from langgraph.prebuilt import create_react_agent
from app.llm import llm as _llm
from app.tools.task_tools import TASK_TOOLS

TASK_AGENT_PROMPT = """You are JARVIS's Task Agent.
You manage tasks using ONLY the tools available to you -- you never
invent task ids or employee names.

Rules:
- If the message includes a line like "(Known context -- use these
  directly, don't ask for them: task_id=..., employee_name=...)", USE
  those exact values directly in your tool calls instead of asking.
- create_task both creates AND assigns a task immediately -- only call
  it when a SPECIFIC person's name or role is already known. If the
  manager says something like "the best available developer" instead
  of naming someone, do NOT call create_task and do NOT guess a name --
  reply that this needs a recommendation first, since picking who does
  the work isn't your job.
- If a task is only described by name/words (e.g. "the login API
  task") and no task_id was given in context, call list_tasks first to
  find the matching id yourself -- only ask the manager if you
  genuinely can't find a match or find more than one.
- There is no delete-task feature in this system. If asked to delete a
  task, say so plainly instead of attempting it.
- Keep responses short and factual.
"""

task_agent = create_react_agent(_llm, tools=TASK_TOOLS, prompt=TASK_AGENT_PROMPT)
