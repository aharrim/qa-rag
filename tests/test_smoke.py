# tests/test_smoke.py

import os
import sys
import io
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
# Test utilities
# -------------------------
def capture_output(func, *args, **kwargs) -> str:
    """
    Run a function and capture everything it prints.
    """
    buf = io.StringIO()
    with redirect_stdout(buf):
        func(*args, **kwargs)
    return buf.getvalue()


def assert_contains(text: str, expected: str):
    assert expected in text, f"Expected to find '{expected}' in output"


def assert_not_contains(text: str, unexpected: str):
    assert unexpected not in text, f"Did NOT expect to find '{unexpected}' in output"


# -------------------------
# Build shared state ONCE
# -------------------------
print("\n>>> Building QA-RAG state for tests")

state = build_state_from_csv_or_memory(
    bugs_in_memory=None,
    CSV_PATH=os.path.join(PROJECT_ROOT, "bugs_sample_20.csv"),
)

print(">>> State ready")
print(">>> Bugs loaded:", len(state.bugs))


# ============================================================
# TESTS (YOU WILL IMPLEMENT THESE)
# ============================================================

def test_open_bugs_count_for_component():
    """
    Question:
      how many open bugs for payments?
    """
    question = "how many open bugs for payments?"

    output = capture_output(answer_question, state, question)

    # Compute expected count from state
    expected_count = (
        state.open_by_component
        .loc[state.open_by_component["component"].str.lower() == "payments", "open_bugs"]
        .iloc[0]
    )
    print("expected count : ", expected_count)
    # Assert the number appears in output
    assert str(expected_count) in output



def test_rag_known_bug_apple_pay_pending():
    """
    RAG Question:
      Is there a known bug where Apple Pay succeeds but order stays pending?

    Goal:
      Make sure RAG retrieval returns BUG-1005 in the printed "Top Matches".
    """
    question = "Is there a known bug where Apple Pay succeeds but order stays pending?"

    output = capture_output(answer_question, state, question)

    # TODO 1: Assert router chose RAG
    # Example expectation in output: "[Router] Route = RAG"
    # assert "Route = RAG" in output
    assert "[Router] Route = RAG" in output

    # TODO 2: Assert the top matches include BUG-1005
    # We are NOT testing the LLM answer here (keep it minimal).
    # We only test retrieval printed results.
    #
    # Example expectation in output: "BUG-1005"
    # assert "BUG-1005" in output
    expected_bug = "BUG-1005"
    assert_contains(output,expected_bug)


def test_rag_safe_refusal_for_vague_question():
    """
    RAG + Grounding test:
      App is slow sometimes and feels buggy?

    Goal:
      When retrieval is weak / vague, the app should NOT hallucinate.
      It should print the Safe Refusal message.

    We are NOT testing the LLM answer content here.
    We only verify the grounding behavior (refusal path).
    """
    question = "App is slow sometimes and feels buggy?"

    output = capture_output(answer_question, state, question)
    print(output)
    # TODO 1: Assert router chose RAG (keep it minimal)
    # Example in output: "[Router] Route = RAG"
    # assert "Route = RAG" in output
    assert_contains(output, "Route = RAG")

    # TODO 2: Assert it went to safe refusal path (grounding)
    # Example in output: "=== Final Answer (Safe Refusal) ==="
    # assert "Safe Refusal" in output
    assert_contains(output, "Safe Refusal")

    # TODO 3 (optional): Assert it includes the "not enough evidence" wording
    # (depends on your exact format_safe_refusal text)
    assert "Not enough evidence" in output
    # assert_contains(output, "Not enough evidence")

    




def test_closed_bugs_count_for_component():
    """
    Question:
      how many closed bugs for checkout?
    """
    question = "how many closed bugs for checkout?"

    output = capture_output(answer_question, state, question)

    # TODO:
    # 1) Compute expected count from state.df
    # 2) Assert the number appears in output
    pass


def test_list_open_bugs_for_component():
    """
    Question:
      list the open bugs for payments
    """
    question = "list the open bugs for payments"

    output = capture_output(answer_question, state, question)

    # TODO:
    # 1) Collect expected bug IDs from state.df
    # 2) Assert EACH ID appears in output
    pass


def test_list_closed_bugs_for_component():
    """
    Question:
      list closed bugs for auth
    """
    question = "list closed bugs for auth"

    output = capture_output(answer_question, state, question)

    # TODO:
    # 1) Collect expected closed bug IDs for Auth
    # 2) Assert EACH ID appears in output
    pass


def test_median_resolution_time():
    """
    Question:
      what’s the median resolution time for checkout?
    """
    question = "what’s the median resolution time for checkout?"

    output = capture_output(answer_question, state, question)

    # TODO:
    # 1) Compute median from state.df (closed only, Checkout)
    # 2) Format it as your app prints it
    # 3) Assert it appears in output
    pass


def test_list_critical_bugs_for_component():
    """
    Question:
      list critical bugs for payments
    """
    question = "list critical bugs for payments"

    output = capture_output(answer_question, state, question)

    # TODO:
    # 1) Collect expected P0 open bug IDs for Payments
    # 2) Assert they appear in output
    pass


# ============================================================
# Simple runner (no pytest needed)
# ============================================================
if __name__ == "__main__":
    tests = [
        test_open_bugs_count_for_component,
        test_closed_bugs_count_for_component,
        test_list_open_bugs_for_component,
        test_list_closed_bugs_for_component,
        test_median_resolution_time,
        test_list_critical_bugs_for_component,
    ]

    passed = 0
    failed = 0

    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {t.__name__}")
            print("   ", e)
            failed += 1

    print("\n======================")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
