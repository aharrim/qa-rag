print(">>> run.py started")

import os, sys
os.environ["TOKENIZERS_PARALLELISM"] = "false"


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

print(">>> src path added:", SRC_PATH)

from qa_rag.app import build_state_from_csv_or_memory, answer_question
print(">>> imported qa_rag.app successfully")

state = build_state_from_csv_or_memory(
    bugs_in_memory=[],  # empty list means: load from CSV if it exists
    CSV_PATH=os.path.join(PROJECT_ROOT, "bugs_sample_20.csv"),
    collection_name="bugs",
    MODEL="llama-3.1-8b-instant",
)

print(">>> state.MODEL =", state.MODEL)

print(">>> state built successfully")

#print("\n>>> Q1 (analytics): how many open bugs for payments?")
#answer_question(state, "how many open bugs?")

print("\n>>> Q2 (RAG): Is there a known bug where Apple Pay succeeds but order stays pending?")
answer_question(state, "Is there a known bug where Apple Pay succeeds but order stays pending?")
