# tests/test_smoke_pytest.py

import os
import sys
import io
import pytest
from contextlib import redirect_stdout

# -------------------------
# Make src/ importable
# -------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")

if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# -------------------------
# Imports from your app
# -------------------------
from qa_rag.app import build_state_from_csv_or_memory, answer_question


# -------------------------
# Test utilities (same as yours)
# -------------------------
def capture_output(func, *args, **kwargs) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        func(*args, **kwargs)
    return buf.getvalue()


def assert_contains(text: str, expected: str):
    assert expected in text, f"Expected to find '{expected}' in output"


# -------------------------
# Shared state (pytest fixture)
# -------------------------
@pytest.fixture(scope="session")
def state():
    return build_state_from_csv_or_memory(
        bugs_in_memory=None,
        CSV_PATH=os.path.join(PROJECT_ROOT, "bugs_sample_20.csv"),
    )


# ============================================================
# TEST 1 — Analytics
# ============================================================
def test_open_bugs_count_for_component(state):
    """
    Question:
      how many open bugs for payments?
    """
    question = "how many open bugs for payments?"

    output = capture_output(answer_question, state, question)

    expected_count = (
        state.open_by_component
        .loc[state.open_by_component["component"].str.lower() == "payments", "open_bugs"]
        .iloc[0]
    )

    assert str(expected_count) in output


# ============================================================
# TEST 2 — RAG retrieval (NOT LLM answer)
# ============================================================
def test_rag_known_bug_apple_pay_pending(state):
    """
    RAG Question:
      Is there a known bug where Apple Pay succeeds but order stays pending?

    Goal:
      Retrieval should surface BUG-1005
    """
    question = "Is there a known bug where Apple Pay succeeds but order stays pending?"

    output = capture_output(answer_question, state, question)

    assert_contains(output, "Route = RAG")
    assert_contains(output, "BUG-1005")


# ============================================================
# TEST 3 — Grounding (safe refusal)
# ============================================================
def test_grounding_safe_refusal_when_evidence_is_weak(state):
    """
    Question:
      App is slow sometimes and feels buggy?

    Goal:
      Grounding layer should refuse (no hallucination)
    """
    question = "App is slow sometimes and feels buggy?"

    output = capture_output(answer_question, state, question)

    assert_contains(output, "Safe Refusal")
    assert_contains(output, "Not enough evidence")
