from langgraph.prebuilt import create_react_agent
from app.llm import llm as _llm
from app.tools.analytics_tools import ANALYTICS_TOOLS

ANALYTICS_PROMPT = """You are JARVIS's Analytics Agent. Answer questions
about project progress and workload using only your tools. Summarize
numbers plainly (e.g. '7 of 12 tasks done, on track'). Never invent
figures you haven't fetched."""

analytics_agent = create_react_agent(_llm, tools=ANALYTICS_TOOLS, prompt=ANALYTICS_PROMPT)
