"""
Live demo script -- REVISED to match Narendra's real API contract.

Walks through: manager asks who should do a task -> Supervisor routes
to the Employee Recommendation lane -> gets a real ranked list from
Narendra's /recommendations, stages a real proposal -> manager says
"yes" -> the graph approves the proposal, which really allocates the
task via Narendra's /proposals/{id}/approve.

USAGE:
  1. Put your keys in .env:
       GROQ_API_KEY=your-groq-key
       PARTNER_API_KEY=whatever Narendra gives you (use "test-key" for
       the bundled mock backend, which already expects that exact value)
  2. Run: python demo.py
"""
import os
import subprocess
import sys
import time
import asyncio
import httpx
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

MOCK_PORT = 9000
os.environ["BACKEND_BASE_URL"] = f"http://localhost:{MOCK_PORT}/api/v1"
os.environ.setdefault("PARTNER_API_KEY", "test-key")  # matches the mock backend's expected key


def _banner(text: str):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def _step(n: str, text: str):
    print(f"\n--- Step {n}: {text} ---")


def _wait_for_backend(url: str, timeout: int = 10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            httpx.get(url, headers={"X-API-Key": os.environ["PARTNER_API_KEY"]}, timeout=1.0)
            return True
        except Exception:
            time.sleep(0.3)
    return False


async def run_demo():
    from app.graph import jarvis_graph

    _banner('JARVIS DEMO -- Manager: "Who should fix the login bug?"')

    _step("1", "Manager asks who should take the task")
    state = {"input_text": "who should fix the login bug, it needs python fastapi auth skills"}
    result = await jarvis_graph.ainvoke(state)
    print(f"JARVIS: {result.get('result')}")
    proposal_id = result.get("proposal_id")
    print(f"(Recommended: {result.get('recommended_employee_name')}, staged as proposal #{proposal_id})")
    assert result.get("requires_confirmation") is True, "Expected a pending proposal here."

    _step("2", "Manager confirms with a bare 'yes' -- no need to repeat the task")
    state = {"input_text": "yes, go ahead", "proposal_id": proposal_id, "confirmed": True}
    result = await jarvis_graph.ainvoke(state)
    print(f"JARVIS: {result.get('result')}")

    _step("3", "Verify a real task now exists, stamped as AI-proposed")
    key = os.environ["PARTNER_API_KEY"]
    tasks = httpx.get(f"http://localhost:{MOCK_PORT}/api/v1/tasks", headers={"X-API-Key": key}).json()
    ai_tasks = [t for t in tasks if t.get("proposed_by") == "ai"]
    for t in ai_tasks:
        print(f"  task #{t['id']}: {t['member']} -> {t['task']!r} (proposed_by={t['proposed_by']})")

    _banner("DEMO COMPLETE")


def main():
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: put GROQ_API_KEY=your-key in a .env file before running this demo.")
        sys.exit(1)

    print("Starting mock backend (mirrors Narendra's real API contract)...")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_backend.main:app", "--port", str(MOCK_PORT), "--log-level", "warning"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        if not _wait_for_backend(f"http://localhost:{MOCK_PORT}/api/v1/employees"):
            print("ERROR: mock backend didn't start in time.")
            sys.exit(1)
        asyncio.run(run_demo())
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()
