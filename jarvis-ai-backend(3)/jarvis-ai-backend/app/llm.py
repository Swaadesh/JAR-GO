"""
One place that builds the LLM client every agent uses.

Why this file exists: every agent used to instantiate ChatAnthropic
directly, so switching providers meant editing 5 files. Now they all
import `llm` from here instead -- switching providers again later means
editing only this file.
"""
from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY, GROQ_MODEL

llm = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0)
