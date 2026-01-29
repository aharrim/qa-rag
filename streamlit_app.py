import os
import sys
import textwrap
import io
from contextlib import redirect_stdout

import streamlit as st

# -------------------------
# Env (match Streamlit Cloud behavior)
# -------------------------
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
# Demo questions (product-style)
# -------------------------
DEMO_QUESTIONS = {
    "Release readiness": "Give me a release readiness summary: total open bugs, total critical (P0) open bugs, and top risky components.",
    "Open bugs by component": "How many open bugs by component?",
    "Critical bugs (P0)": "What are the critical bugs for all bugs?",
    "Bug lookup (example)": "Show details for BUG-1005.",
    "Closed bugs for component": "What are the closed bugs for component Payments?",
    "Avg resolution time by component": "What is the average resolution time (days) by component for closed bugs?",
    "Resolution time for bug": "What is the resolution time for BUG-1005?",
    "Known issue (Apple Pay pending)": "Is there a known bug where Apple Pay succeeds but order stays pending?",
}


# -------------------------
# Helpers
# -------------------------
def normalize_question(q: str) -> str:
    return " ".join((q or "").strip().split())


def wrap(s: str, width: int = 110) -> str:
    return "\n".join(textwrap.fill(line, width=width) for line in (s or "").splitlines())


def set_question(q: str) -> None:
    st.session_state["question"] = q


def extract_route(out: str) -> str | None:
    # Example: "[Router] Route = RAG"
    for ln in (out or "").splitlines():
        if "Route" in ln and "Router" in ln and "=" in ln:
            return ln.strip()
    return None


def parse_output(out: str):
    """
    Parse printed output into:
    - final_answer: the main answer block (grounded answer)
    - top_matches: the RAG top matches section
    - route_line: router line
    - other: everything else (logs/details)
    """
    lines = (out or "").splitlines()
    route_line = extract_route(out)

    final_answer_lines = []
    top_matches_lines = []
    other_lines = []

    in_final = False
    in_matches = False

    for ln in lines:
        s = ln.strip()

        # Section toggles
        if s.startswith("=== Final Answer"):
            in_final = True
            in_matches = False
            continue  # skip header line
        if s.startswith("=== RAG Top Matches"):
            in_matches = True
            in_final = False
            continue  # skip header line

        # If another section header starts, stop current section
        if s.startswith("===") and not s.startswith("=== Final Answer") and not s.startswith("=== RAG Top Matches"):
            in_final = False
            in_matches = False
            other_lines.append(ln)
            continue

        # Route line: don't duplicate in other blocks
        if route_line and ln.strip() == route_line.strip():
            continue

        if in_final:
            final_answer_lines.append(ln)
        elif in_matches:
            top_matches_lines.append(ln)
        else:
            other_lines.append(ln)

    final_answer = "\n".join(final_answer_lines).strip()
    top_matches = "\n".join(top_matches_lines).strip()
    other = "\n".join(other_lines).strip()

    return final_answer, top_matches, route_line, other


# -------------------------
# UI
# -------------------------
st.set_page_config(page_title="QA-RAG", layout="wide")

# Header bar
h1, h2 = st.columns([3, 2])
with h1:
    st.title("QA-RAG")
    st.caption("Bug Intelligence — grounded answers + retrieval context")
with h2:
    st.empty()

# Sidebar
st.sidebar.header("Quick demos")
st.sidebar.caption("Pick a scenario to auto-fill the question.")

for label, q in DEMO_QUESTIONS.items():
    st.sidebar.button(label, on_click=set_question, args=(q,), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("You can also type your own question.")


# -------------------------
# Load state
# -------------------------
csv_path = os.path.join(PROJECT_ROOT, "bugs_sample_20.csv")

@st.cache_resource
def load_state():
    return build_state_from_csv_or_memory(
        bugs_in_memory=[],
        CSV_PATH=csv_path,
        collection_name="bugs",
    )

state = load_state()

# Minimal info row
info1, info2, info3 = st.columns([1, 2, 2])
with info1:
    st.metric("Bugs loaded", len(state.bugs))
with info2:
    st.caption(f"Dataset: `{os.path.basename(csv_path)}`")
with info3:
    st.caption(f"Model: `{getattr(state, 'MODEL', 'unknown')}`")

st.divider()

# Input + actions
if "question" not in st.session_state:
    st.session_state["question"] = "Is there a known bug where Apple Pay succeeds but order stays pending?"

row = st.columns([6, 1, 1])
with row[0]:
    st.text_input("Ask a question", key="question", placeholder="e.g., How many open bugs by component?")
with row[1]:
    run = st.button("Run", type="primary", use_container_width=True)
with row[2]:
    clear = st.button("Clear", use_container_width=True)

if clear:
    st.session_state["question"] = ""
    st.rerun()

# Output
if run:
    q_norm = normalize_question(st.session_state["question"])
    if not q_norm:
        st.warning("Type a question.")
    else:
        buf = io.StringIO()
        err = None

        try:
            with st.spinner("Running..."):
                with redirect_stdout(buf):
                    answer_question(state, q_norm)
        except Exception as e:
            err = e

        out = buf.getvalue().strip()

        if err:
            st.error(f"Error: {err}")

        final_answer, top_matches, route_line, other = parse_output(out)

        st.subheader("Result")

        # Main: Final Answer (grounded answer)
        with st.container(border=True):
            if route_line:
                st.caption(route_line)

            title = "Answer"
            st.markdown(f"#### {title}")

            if final_answer:
                st.markdown(wrap(final_answer))
            else:
                # Fallback: if Final Answer header wasn't present, show wrapped full text
                st.markdown(wrap(out) if out else "No output.")

        # Secondary boxes
        col_a, col_b = st.columns(2)

        with col_a:
            with st.container(border=True):
                st.markdown("#### Top matches")
                if top_matches:
                    st.code(top_matches, language="text")
                else:
                    st.caption("No top matches available for this query.")

        with col_b:
            with st.container(border=True):
                st.markdown("#### Details")
                if other.strip():
                    st.code(other.strip(), language="text")
                else:
                    st.caption("No extra details.")

        # Raw output (optional, hidden)
        with st.expander("Raw output"):
            st.code(out if out else "(no output)", language="text")

