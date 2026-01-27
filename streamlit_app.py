# import os
# import sys
# import textwrap
# import streamlit as st

# # -------------------------
# # Make src/ importable FIRST
# # -------------------------
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# SRC_PATH = os.path.join(PROJECT_ROOT, "src")
# if SRC_PATH not in sys.path:
#     sys.path.insert(0, SRC_PATH)

# from qa_rag.app import build_state_from_csv_or_memory, answer_question


# # -------------------------
# # Small helpers
# # -------------------------
# def normalize_question(q: str) -> str:
#     return " ".join((q or "").strip().split())


# def wrap(s: str, width: int = 110) -> str:
#     return "\n".join(textwrap.fill(line, width=width) for line in (s or "").splitlines())


# # -------------------------
# # Streamlit UI
# # -------------------------
# st.set_page_config(page_title="QA-RAG Demo", layout="centered")
# st.title("QA-RAG Demo (Bugs RAG + Analytics)")

# csv_path = os.path.join(PROJECT_ROOT, "bugs_sample_20.csv")


# @st.cache_resource
# def load_state():
#     # This should:
#     # - load CSV
#     # - build analytics routing
#     # - build / reuse chroma collection
#     # - wire LLM client (Groq)
#     return build_state_from_csv_or_memory(
#         bugs_in_memory=[],
#         CSV_PATH=csv_path,
#         collection_name="bugs",
#         # If your app supports it:
#         # MODEL="llama-3.1-8b-instant",
#     )


# state = load_state()
# st.caption(f"Loaded bugs: {len(state.bugs)} | CSV: {os.path.basename(csv_path)}")

# question = st.text_input(
#     "Ask a question",
#     value="Which component has the most open critical bugs?",
# )

# col1, col2 = st.columns([1, 1])
# with col1:
#     run = st.button("Run", use_container_width=True)
# with col2:
#     clear = st.button("Clear", use_container_width=True)

# if clear:
#     st.session_state["q"] = ""
#     st.rerun()

# if run:
#     q = normalize_question(question)
#     if not q:
#         st.warning("Type a question.")
#     else:
#         import io
#         from contextlib import redirect_stdout

#         buf = io.StringIO()
#         with redirect_stdout(buf):
#             answer_question(state, q)

#         out = buf.getvalue().strip()
#         st.subheader("Output")
#         st.code(wrap(out), language="text")





import os
import sys
import textwrap

import streamlit as st
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HOME", ".hf_cache")
# -------------------------
# Make src/ importable
# -------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from qa_rag.app import build_state_from_csv_or_memory, answer_question


# -------------------------
# Small text wrappers
# -------------------------
def normalize_question(q: str) -> str:
    return " ".join((q or "").strip().split())


def wrap(s: str, width: int = 110) -> str:
    return "\n".join(textwrap.fill(line, width=width) for line in (s or "").splitlines())


# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="QA-RAG Demo", layout="centered")
st.title("QA-RAG Demo (Bugs RAG + Analytics)")

csv_path = os.path.join(PROJECT_ROOT, "bugs_sample_20.csv")

# This caches the heavy init (CSV load + chroma collection build + embeddings model load)
@st.cache_resource
def load_state():
    return build_state_from_csv_or_memory(
        bugs_in_memory=[],
        CSV_PATH=csv_path,
        collection_name="bugs",
        # MODEL can be overridden here if you want:
        # MODEL="llama-3.1-8b-instant",
    )


state = load_state()

st.caption(f"Loaded bugs: {len(state.bugs)} | CSV: {os.path.basename(csv_path)}")

question = st.text_input(
    "Ask a question",
    value="Is there a known bug where Apple Pay succeeds but order stays pending?",
)

run = st.button("Run")

if run:
    q = normalize_question(question)
    if not q:
        st.warning("Type a question.")
    else:
        # capture printed output from your existing answer_question
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                answer_question(state, q)
        except Exception as e:
            st.error(f"Error: {e}")

        out = buf.getvalue().strip()

        st.subheader("Output")
        st.code(wrap(out) if out else "(no output)", language="text")
