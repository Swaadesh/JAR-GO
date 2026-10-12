"""
Central config for the AI Backend layer.

Everything here is read from environment variables so no keys or URLs
ever get hardcoded (per the team rule: no API keys in source).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Narendra's real backend. Base URL already includes the /api/v1 prefix,
# so every tool path below is relative to that (e.g. "/employees", not
# "/api/v1/employees" and definitely not "/api/employees" like the old
# placeholder paths).
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000/api/v1")

# Narendra's auth: a single shared secret sent as X-API-Key, not a Bearer
# token. Get the real value from him -- do not commit it.
PARTNER_API_KEY = os.getenv("PARTNER_API_KEY", "")

# LLM provider -- Groq (OpenAI-compatible, free/fast tier commonly used
# for hackathon-style builds). Swap this whole block if you switch
# providers later; nothing else in the codebase needs to change since
# every agent imports its LLM from app/llm.py.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


# Real gate rule (Narendra's, mirrored here): only AI-picked assignments
# (via recommend -> propose -> approve) need manager confirmation. Direct
# allocation, where the manager already named the person, does not.
HTTP_TIMEOUT_SECONDS = 15.0
