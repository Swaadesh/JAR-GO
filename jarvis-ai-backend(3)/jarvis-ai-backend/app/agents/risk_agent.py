from langgraph.prebuilt import create_react_agent
from app.llm import llm as _llm
from app.tools.risk_tools import RISK_TOOLS

RISK_PROMPT = """You are JARVIS's Risk Agent. Surface overdue tasks,
overloaded employees, and stalled work using only your tools. For each
risk you flag, state what it is, who/what it affects, and one concrete
suggested action. Do not take any action yourself -- you only report."""

risk_agent = create_react_agent(_llm, tools=RISK_TOOLS, prompt=RISK_PROMPT)
