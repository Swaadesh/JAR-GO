# JARVIS AI Backend & Integration (Swaadesh's part)

LangGraph multi-agent layer for JARVIS, now wired to Narendra's REAL
API contract (not a guess -- based on his own spec message).

## Big change from the first version: the overlap with Narendra's work

Narendra independently built two things that overlap with what this
layer originally did on its own:
- Employee recommendation scoring (`POST /recommendations`)
- The manager-confirmation gate for AI-picked assignments
  (`POST /proposals` -> `/proposals/{id}/approve` or `/reject`)

Rather than keep two systems that could disagree, **this AI layer now
calls his endpoints for both** instead of scoring/gating on its own.
What's still genuinely this layer's own work, with no equivalent on
his side:
- The Supervisor + LangGraph multi-agent routing (his system is a
  single flat tool-calling agent, no supervisor/specialist split)
- The Task, Analytics, and Risk agents as distinct reasoning agents
- Turning his raw scores/reasons into a manager-facing explanation

## Layout

```
app/
  config.py                 env-driven settings
  llm.py                    single shared Groq client every agent imports
  state.py                  shared LangGraph state
  tools/
    _client.py               shared HTTP client -> Narendra's real API (X-API-Key auth)
    task_tools.py             list/get/create/complete/reassign task (real endpoints)
    employee_tools.py        list/get employee (workload/availability come inline)
    proposal_tools.py        get_recommendations, stage/approve/reject proposal
    analytics_tools.py       team + per-employee task summaries (no /analytics/* endpoint exists)
    risk_tools.py             overloaded / overdue employees, from live employee data
  agents/
    supervisor.py             classifies command -> task/recommendation/analytics/risk
    task_agent.py             direct allocation ONLY when a person is already named
    employee_recommendation_agent.py   calls Narendra's /recommendations + stages a proposal
    analytics_agent.py, risk_agent.py
  graph.py                   routing + the REAL confirmation flow (see below)
  voice.py                   still a stub -- Narendra already has a working
                              Sarvam STT/TTS pipeline in his repo, worth
                              reusing instead of building a second one
  main.py                    FastAPI app exposing POST /api/ai/command
tests/
  test_supervisor_and_gating.py   10 passing tests, no live calls needed
mock_backend/
  main.py                    mirrors Narendra's REAL contract (not a
                              fictional one) -- same paths, same auth
                              header, same proposal single-slot behavior
demo.py                      live demo: recommend -> confirm -> approve
```

## The confirmation model, precisely

This is the part most worth double-checking with Narendra before your
demo, because it's now based on his design, not an assumption:

- `POST /tasks` (direct allocation) has **no gate at all** -- it both
  creates and assigns in one call. Per his rule, this is only supposed
  to be used when a specific person is already named.
- The **only** thing requiring manager confirmation is when the AI
  itself picks who does the work. That flow is: `get_recommendations`
  (read-only) -> `stage_proposal` -> manager says yes/no ->
  `approve_proposal` or `reject_proposal`.
- **Caveat (his design, not a gap introduced here):** nothing on the
  server enforces that "a specific person was already named" before
  `create_task` is called -- that's judgment left entirely to whichever
  agent calls it. Here, that judgment lives in the Task Agent's prompt
  (it's explicitly told to refuse to guess a name and hand off to the
  recommendation lane instead). Worth being aware this is a prompt-level
  rule, not a hard server-side check, on either side of this integration.
- Only one proposal can be pending globally at a time (shared with his
  voice assistant too, per his note) -- the graph approves or rejects
  right after staging, never leaves one sitting.

## Verified (what was actually run, not just written)

No real `GROQ_API_KEY` or `PARTNER_API_KEY` was available in this dev
environment, so LLM explanation calls were stubbed for these specific
checks -- everything else below is real HTTP calls, not mocked:

- Full recommend -> stage proposal -> approve -> task-created flow, run
  through an in-process ASGI transport against the mock backend (which
  mirrors Narendra's real contract exactly): correctly picked the
  better-skill-matched candidate, staged proposal #1, approved it, and
  a real new task appeared in the task list stamped `proposed_by: "ai"`.
- The same flow run through the **actual compiled LangGraph** (not just
  the agent function directly): a bare "yes go ahead" with no explicit
  intent correctly bypassed normal Supervisor routing and went straight
  to approval.
- `pytest tests/` passes 10/10: keyword routing (including the
  assign-vs-recommend regression case) and all 5 confirmation-routing
  cases (approve on "yes", reject on "no", ignoring stray "yes" with
  nothing pending, etc).
- `demo.py` itself run end-to-end with a placeholder Groq key: gets
  through starting the mock backend, real recommendation HTTP calls,
  and proposal staging correctly, failing only at the actual Groq call
  (blocked by this sandbox's network policy, not a code issue) --
  confirmed the mock server also shuts down cleanly on failure.

NOT yet verified -- needs your real keys to check:
- Whether the LLM-generated explanation text actually reads well.
- The Task Agent's judgment calls in practice (whether it reliably
  refuses to guess a name vs. correctly using one it was given).
- Analytics/Risk agents' tool-calling behavior with a live model.
- Voice end-to-end (still unbuilt here -- see note below).

## Try it right now

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY; PARTNER_API_KEY=test-key works against the bundled mock
python demo.py
```

Once Narendra sends the real `PARTNER_API_KEY`, switch
`BACKEND_BASE_URL` to his real server and drop the mock backend
entirely -- nothing else in the code needs to change, since the mock
mirrors his real contract.

## Voice

Narendra already has a working Sarvam STT/TTS + Groq tool-calling
pipeline in his repo (`voice.py`). Given that, building a second voice
pipeline here would be more duplication -- worth discussing whether
your agents plug into his voice input/output instead of building your
own from scratch.

## Setup

```bash
pip install -r requirements.txt
python demo.py
pytest tests/ -v
```
