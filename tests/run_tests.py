# tests/run_tests.py
import os, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")

# Make tests/ and project root importable
for p in [PROJECT_ROOT, TESTS_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from test_smoke import (
    test_open_bugs_count_for_component,
    test_rag_known_bug_apple_pay_pending,
    test_rag_safe_refusal_for_vague_question  # <-- your new test
)

if __name__ == "__main__":
    test_open_bugs_count_for_component()
    test_rag_known_bug_apple_pay_pending()
    test_rag_safe_refusal_for_vague_question()
    print("✅ smoke tests passed")

