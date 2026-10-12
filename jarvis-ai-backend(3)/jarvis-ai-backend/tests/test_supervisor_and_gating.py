"""
Fast tests that don't require a live LLM call or the real backend --
keyword routing and the confirmation-entry routing are both
deterministic. Run: pytest tests/ -v
"""
import pytest
from app.agents.supervisor import classify_intent
from app.graph import route_from_entry


@pytest.mark.asyncio
async def test_classify_intent_task():
    assert await classify_intent("create task fix login bug") == "task"


@pytest.mark.asyncio
async def test_classify_intent_recommendation():
    assert await classify_intent("recommend the best available developer") == "employee_recommendation"


@pytest.mark.asyncio
async def test_classify_intent_risk():
    assert await classify_intent("show me overdue tasks") == "risk"


@pytest.mark.asyncio
async def test_classify_intent_analytics():
    assert await classify_intent("give me the progress report") == "analytics"


@pytest.mark.asyncio
async def test_classify_intent_assign_beats_recommendation_keywords():
    # Regression test: this exact phrase contains both an action verb
    # ("assign") and a recommendation-sounding phrase ("best available").
    # It must route to "task" so the Task Agent's prompt (not a random
    # LLM guess) is what decides whether a name was actually given.
    text = "assign the login API task to the best available developer"
    assert await classify_intent(text) == "task"


def test_route_from_entry_goes_to_supervisor_with_no_pending_proposal():
    state = {"input_text": "assign it to whoever is best", "proposal_id": None}
    assert route_from_entry(state) == "supervisor"


def test_route_from_entry_approves_on_confirm_word():
    state = {"input_text": "yes confirm that", "proposal_id": 5}
    assert route_from_entry(state) == "approve"


def test_route_from_entry_approves_on_confirmed_flag():
    state = {"input_text": "go ahead", "proposal_id": 5, "confirmed": True}
    assert route_from_entry(state) == "approve"


def test_route_from_entry_rejects_on_decline_word():
    state = {"input_text": "no, cancel that", "proposal_id": 5}
    assert route_from_entry(state) == "reject"


def test_route_from_entry_ignores_confirm_words_without_pending_proposal():
    # "yes" with nothing staged shouldn't hijack normal routing.
    state = {"input_text": "yes I need help with something else", "proposal_id": None}
    assert route_from_entry(state) == "supervisor"
