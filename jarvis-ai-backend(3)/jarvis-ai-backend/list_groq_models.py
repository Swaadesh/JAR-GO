"""
Run this once to see exactly which models YOUR Groq account can use.
Usage: python list_groq_models.py
"""
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
models = client.models.list()
print("Models available on your account:\n")
for m in models.data:
    print(f"  {m.id}")
