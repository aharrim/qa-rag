# import os
# import sys
# import textwrap
# import io
# from contextlib import redirect_stdout

# import streamlit as st

# # -------------------------
# # Env (match Streamlit Cloud behavior)
# # -------------------------
# os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# os.environ.setdefault("HF_HOME", ".hf_cache")

# # -------------------------
# # Make src/ importable
# # -------------------------
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# SRC_PATH = os.path.join(PROJECT_ROOT, "src")
# if SRC_PATH not in sys.path:
#     sys.path.insert(0, SRC_PATH)

# from qa_rag.app import build_state_from_csv_or_memory, answer_question


# # -------------------------
# # Demo questions (product-style)
# # -------------------------
# DEMO_QUESTIONS = {
#     "Release readiness": "Give me a release readiness summary: total open bugs, total critical (P0) open bugs, and top risky components.",
#     "Open bugs by component": "How many open bugs by component?",
#     "Critical bugs (P0)": "What are the critical bugs for all bugs?",
#     "Bug lookup (example)": "Show details for BUG-1005.",
#     "Closed bugs for component": "What are the closed bugs for component Payments?",
#     "Avg resolution time by component": "What is the average resolution time (days) by component for closed bugs?",
#     "Resolution time for bug": "What is the resolution time for BUG-1005?",
#     "Known issue (Apple Pay pending)": "Is there a known bug where Apple Pay succeeds but order stays pending?",
# }


# # -------------------------
# # Helpers
# # -------------------------
# def normalize_question(q: str) -> str:
#     return " ".join((q or "").strip().split())


# def wrap(s: str, width: int = 110) -> str:
#     return "\n".join(textwrap.fill(line, width=width) for line in (s or "").splitlines())


# def set_question(q: str) -> None:
#     st.session_state["question"] = q


# def extract_route(out: str) -> str | None:
#     # Example: "[Router] Route = RAG"
#     for ln in (out or "").splitlines():
#         if "Route" in ln and "Router" in ln and "=" in ln:
#             return ln.strip()
#     return None


# def parse_output(out: str):
#     """
#     Parse printed output into:
#     - final_answer: the main answer block (grounded answer)
#     - top_matches: the RAG top matches section
#     - route_line: router line
#     - other: everything else (logs/details)
#     """
#     lines = (out or "").splitlines()
#     route_line = extract_route(out)

#     final_answer_lines = []
#     top_matches_lines = []
#     other_lines = []

#     in_final = False
#     in_matches = False

#     for ln in lines:
#         s = ln.strip()

#         # Section toggles
#         if s.startswith("=== Final Answer"):
#             in_final = True
#             in_matches = False
#             continue  # skip header line
#         if s.startswith("=== RAG Top Matches"):
#             in_matches = True
#             in_final = False
#             continue  # skip header line

#         # If another section header starts, stop current section
#         if s.startswith("===") and not s.startswith("=== Final Answer") and not s.startswith("=== RAG Top Matches"):
#             in_final = False
#             in_matches = False
#             other_lines.append(ln)
#             continue

#         # Route line: don't duplicate in other blocks
#         if route_line and ln.strip() == route_line.strip():
#             continue

#         if in_final:
#             final_answer_lines.append(ln)
#         elif in_matches:
#             top_matches_lines.append(ln)
#         else:
#             other_lines.append(ln)

#     final_answer = "\n".join(final_answer_lines).strip()
#     top_matches = "\n".join(top_matches_lines).strip()
#     other = "\n".join(other_lines).strip()

#     return final_answer, top_matches, route_line, other


# # -------------------------
# # UI
# # -------------------------
# st.set_page_config(page_title="QA-RAG", layout="wide")

# # Header bar
# h1, h2 = st.columns([3, 2])
# with h1:
#     st.title("QA-RAG")
#     st.caption("Bug Intelligence — grounded answers + retrieval context")
# with h2:
#     st.empty()

# # Sidebar
# st.sidebar.header("Quick demos")
# st.sidebar.caption("Pick a scenario to auto-fill the question.")

# for label, q in DEMO_QUESTIONS.items():
#     st.sidebar.button(label, on_click=set_question, args=(q,), use_container_width=True)

# st.sidebar.markdown("---")
# st.sidebar.caption("You can also type your own question.")


# # -------------------------
# # Load state
# # -------------------------
# csv_path = os.path.join(PROJECT_ROOT, "bugs_sample_20.csv")

# @st.cache_resource
# def load_state():
#     return build_state_from_csv_or_memory(
#         bugs_in_memory=[],
#         CSV_PATH=csv_path,
#         collection_name="bugs",
#     )

# state = load_state()


# # Minimal info row
# info1, info2, info3 = st.columns([1, 2, 2])
# with info1:
#     st.metric("Bugs loaded", len(state.bugs))
# with info2:
#     st.caption(f"Dataset: `{os.path.basename(csv_path)}`")
# with info3:
#     st.caption(f"Model: `{getattr(state, 'MODEL', 'unknown')}`")

# st.divider()

# # Input + actions
# if "question" not in st.session_state:
#     st.session_state["question"] = "Is there a known bug where Apple Pay succeeds but order stays pending?"

# row = st.columns([6, 1, 1])
# with row[0]:
#     st.text_input("Ask a question", key="question", placeholder="e.g., How many open bugs by component?")
# with row[1]:
#     run = st.button("Run", type="primary", use_container_width=True)
# with row[2]:
#     clear = st.button("Clear", use_container_width=True)

# if clear:
#     st.session_state["question"] = ""
#     st.rerun()

# # Output
# if run:
#     q_norm = normalize_question(st.session_state["question"])
#     if not q_norm:
#         st.warning("Type a question.")
#     else:
#         buf = io.StringIO()
#         err = None

#         try:
#             with st.spinner("Running..."):
#                 with redirect_stdout(buf):
#                     answer_question(state, q_norm)
#         except Exception as e:
#             err = e

#         out = buf.getvalue().strip()

#         if err:
#             st.error(f"Error: {err}")

#         final_answer, top_matches, route_line, other = parse_output(out)

#         st.subheader("Result")

#         # Main: Final Answer (grounded answer)
#         with st.container(border=True):
#             if route_line:
#                 st.caption(route_line)

#             title = "Answer"
#             st.markdown(f"#### {title}")

#             # if final_answer:
#             #     st.markdown(wrap(final_answer))
#             # else:
#             #     # Fallback: if Final Answer header wasn't present, show wrapped full text
#             #     st.markdown(wrap(out) if out else "No output.")
            


#             def show_preserved_block(text: str):
#                 text = (text or "").strip()
#                 if not text:
#                     st.caption("No output.")
#                     return

#             # If it contains table-ish spacing, pipes, or many newlines, preserve formatting
#                 looks_tabular = (
#                     "\n" in text
#                     and (
#                     "  " in text  # double spaces (pandas to_string alignment)
#                     or "|" in text
#                     or "component" in text.lower()
#                     or "resolution" in text.lower()
#                     )
#                 )

#                 if looks_tabular:
#                     st.code(text, language="text")
#                 else:
#                     st.markdown(wrap(text))

#             if final_answer:
#                 show_preserved_block(final_answer)
#             else:
#                 show_preserved_block(out if out else "")



#         # Secondary boxes
#         col_a, col_b = st.columns(2)

#         with col_a:
#             with st.container(border=True):
#                 st.markdown("#### Top matches")
#                 if top_matches:
#                     st.code(top_matches, language="text")
#                 else:
#                     st.caption("No top matches available for this query.")

#         with col_b:
#             with st.container(border=True):
#                 st.markdown("#### Details")
#                 if other.strip():
#                     st.code(other.strip(), language="text")
#                 else:
#                     st.caption("No extra details.")

#         # Raw output (optional, hidden)
#         with st.expander("Raw output"):
#             st.code(out if out else "(no output)", language="text")

import os
import sys
import textwrap
import io
from contextlib import redirect_stdout

import pandas as pd
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
from qa_rag.analytics import bugs_to_df, analytics_reports


# -------------------------
# Demo questions (product-style) — keep only 5 (less crowded)
# -------------------------
DEMO_QUESTIONS = {
    "Release readiness": "Give me a release readiness summary: total open bugs, total critical (P0) open bugs, and top risky components.",
    "Open bugs by component": "How many open bugs by component?",
    "Critical bugs (P0)": "What are the critical bugs for all bugs?",
    "Avg resolution time by component": "What is the average resolution time (days) by component for closed bugs?",
    "Known issue: Apple Pay pending": "Is there a known bug where Apple Pay succeeds but order stays pending?",
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
    # Example: "[Router] Route = ANALYTICS"
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

        if s.startswith("=== Final Answer"):
            in_final = True
            in_matches = False
            continue
        if s.startswith("=== RAG Top Matches"):
            in_matches = True
            in_final = False
            continue

        if s.startswith("===") and not s.startswith("=== Final Answer") and not s.startswith("=== RAG Top Matches"):
            in_final = False
            in_matches = False
            other_lines.append(ln)
            continue

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


def show_preserved_block(text: str):
    text = (text or "").strip()
    if not text:
        st.caption("No output.")
        return

    looks_tabular = (
        "\n" in text
        and (
            "  " in text
            or "|" in text
            or "component" in text.lower()
            or "resolution" in text.lower()
        )
    )

    if looks_tabular:
        st.code(text, language="text")
    else:
        st.markdown(wrap(text))


# -------------------------
# Local analytics helpers (keep existing functionality; no extra analytics.py deps)
# -------------------------
def count_by_component(df: pd.DataFrame, count_col_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["component", count_col_name])
    return (
        df.groupby("component")["id"]
        .count()
        .sort_values(ascending=False)
        .rename(count_col_name)
        .reset_index()
    )


def count_by_severity(df: pd.DataFrame, count_col_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["severity", count_col_name])
    sev = df["severity"].fillna("").astype(str).str.strip()
    tmp = df.copy()
    tmp["severity"] = sev.replace("", "unknown")
    return (
        tmp.groupby("severity")["id"]
        .count()
        .sort_values(ascending=False)
        .rename(count_col_name)
        .reset_index()
    )


def apply_filters(df: pd.DataFrame, status: str | None = None, component: str | None = None) -> pd.DataFrame:
    out = df
    if status == "open":
        out = out[out["is_open"]]
    elif status == "closed":
        out = out[~out["is_open"]]
    if component:
        out = out[out["component"].fillna("").astype(str).str.strip() == component]
    return out


def bugs_list_view(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["id", "component", "severity", "created_date", "closed_date", "title"] if c in df.columns]
    if not cols:
        return df
    return df[cols].sort_values(by="created_date", ascending=False, na_position="last")


# -------------------------
# Analytics cache
# -------------------------
@st.cache_data(show_spinner=False)
def compute_analytics_tables(bugs_list: list[dict]) -> dict:
    df = bugs_to_df(bugs_list)

    # Your existing reports
    open_by_component, resolution_by_component, open_critical, open_critical_by_component = analytics_reports(df)

    # Add closed/open by severity and closed by component (computed here)
    closed_by_component = count_by_component(df[~df["is_open"]], "closed_bugs")
    open_by_severity = count_by_severity(df[df["is_open"]], "open_bugs")
    closed_by_severity = count_by_severity(df[~df["is_open"]], "closed_bugs")

    return {
        "df": df,
        "open_by_component": open_by_component,
        "closed_by_component": closed_by_component,
        "open_by_severity": open_by_severity,
        "closed_by_severity": closed_by_severity,
        "resolution_by_component": resolution_by_component,
        "open_critical": open_critical,
        "open_critical_by_component": open_critical_by_component,
    }


# -------------------------
# Question inference
# -------------------------
CLOSED_WORDS = ["closed", "resolved", "fixed", "done", "completed"]
OPEN_WORDS = ["open", "pending", "active"]


def infer_status(q: str) -> str | None:
    ql = (q or "").lower()
    if any(w in ql for w in CLOSED_WORDS):
        return "closed"
    if any(w in ql for w in OPEN_WORDS):
        return "open"
    return None


def infer_component(q: str, df: pd.DataFrame) -> str | None:
    if df is None or df.empty or "component" not in df.columns:
        return None

    ql = (q or "").lower()
    components = (
        df["component"]
        .fillna("")
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    comps_sorted = sorted([c for c in components if c.strip()], key=lambda x: len(x), reverse=True)
    for comp in comps_sorted:
        if comp.lower() in ql:
            return comp

    if "component" in ql:
        tokens = ql.split()
        for i, t in enumerate(tokens):
            if t == "component" and i + 1 < len(tokens):
                guess = tokens[i + 1].strip().lower()
                for comp in comps_sorted:
                    if comp.lower() == guess:
                        return comp

    return None


# -------------------------
# Analytics renderer (table + chart)
# -------------------------
def render_inline_chart_and_table(q: str, tables: dict):
    ql = (q or "").lower()
    df_all: pd.DataFrame = tables["df"]

    status = infer_status(q)
    component = infer_component(q, df_all)

    # Component-specific list query
    if component and status in ("open", "closed") and ("bug" in ql or "bugs" in ql):
        filtered = apply_filters(df_all, status=status, component=component)
        title = f"{status.title()} bugs for {component}"

        st.markdown(f"### {title}")
        st.caption(f"Count: {len(filtered)}")
        st.dataframe(bugs_list_view(filtered), use_container_width=True)

        sev_tbl = count_by_severity(filtered, "bugs")
        if not sev_tbl.empty:
            st.markdown("#### Breakdown by severity")
            st.dataframe(sev_tbl, use_container_width=True)
            st.bar_chart(sev_tbl.set_index("severity")[["bugs"]])
        return

    # Global analytics selection
    if "severity" in ql:
        if status == "closed":
            df_show = tables["closed_by_severity"]
            title = "Closed bugs by severity"
            index_col, value_col = "severity", "closed_bugs"
        else:
            df_show = tables["open_by_severity"]
            title = "Open bugs by severity"
            index_col, value_col = "severity", "open_bugs"

    elif "resolution" in ql or "avg" in ql or "average" in ql or "median" in ql or "p75" in ql or "p90" in ql:
        df_show = tables["resolution_by_component"]
        title = "Resolution time by component"
        index_col = "component"

        if "avg_days" in df_show.columns and ("avg" in ql or "average" in ql):
            value_col = "avg_days"
        elif "median_days" in df_show.columns and "median" in ql:
            value_col = "median_days"
        elif "p75_days" in df_show.columns and "p75" in ql:
            value_col = "p75_days"
        elif "p90_days" in df_show.columns and "p90" in ql:
            value_col = "p90_days"
        else:
            value_col = "median_days" if "median_days" in df_show.columns else df_show.columns[-1]

    elif "critical" in ql or "p0" in ql or "blocker" in ql or "sev0" in ql:
        df_show = tables["open_critical_by_component"]
        title = "Open critical bugs by component"
        index_col = "component"
        value_col = "open_critical_bugs" if "open_critical_bugs" in df_show.columns else df_show.columns[-1]

    else:
        if status == "closed":
            df_show = tables["closed_by_component"]
            title = "Closed bugs by component"
            index_col, value_col = "component", "closed_bugs"
        else:
            df_show = tables["open_by_component"]
            title = "Open bugs by component"
            index_col, value_col = "component", "open_bugs"

    st.markdown(f"### {title}")
    st.dataframe(df_show, use_container_width=True)

    if not df_show.empty and index_col in df_show.columns and value_col in df_show.columns:
        st.bar_chart(df_show.set_index(index_col)[[value_col]])


# -------------------------
# UI
# -------------------------
st.set_page_config(page_title="Bug Intelligence", layout="wide")

# Sidebar: Example questions (less crowded)
st.sidebar.header("Example questions")
st.sidebar.caption("Click to auto-fill the question.")
for label, q in DEMO_QUESTIONS.items():
    st.sidebar.button(label, on_click=set_question, args=(q,), use_container_width=True)

st.sidebar.markdown("---")

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

# Sidebar: Demo dataset (download)
st.sidebar.markdown("### Demo dataset")
with open(csv_path, "rb") as f:
    st.sidebar.download_button(
        label="Download demo CSV",
        data=f.read(),
        file_name="bugs_sample_20.csv",
        mime="text/csv",
        use_container_width=True,
    )

# Header (product name, not “QA-RAG”)
st.title("Bug Intelligence")
st.caption("AI assistant for QA metrics and known issues")



# Minimal info row
info1, info2, info3 = st.columns([1, 2, 2])
with info1:
    st.metric("Bugs loaded", len(state.bugs))
with info2:
    st.caption("Dataset: demo")
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
    run = st.button("Ask", type="primary", use_container_width=True)
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
            with st.spinner("Working..."):
                with redirect_stdout(buf):
                    answer_question(state, q_norm)
        except Exception as e:
            err = e

        out = buf.getvalue().strip()

        if err:
            st.error(f"Error: {err}")

        final_answer, top_matches, route_line, other = parse_output(out)

        st.subheader("Result")

        with st.container(border=True):
            # User-friendly label (no “RAG/Analytics” jargon)
            if route_line:
                if "ANALYTICS" in route_line.upper():
                    st.caption("Result type: metrics")
                elif "RAG" in route_line.upper():
                    st.caption("Result type: explanation (with evidence)")
                else:
                    st.caption("Result type: response")

            st.markdown("#### Answer")

            if final_answer:
                show_preserved_block(final_answer)
            else:
                show_preserved_block(out if out else "")

        # If analytics route, render table + chart inline
        is_analytics = bool(route_line) and ("ANALYTICS" in route_line.upper())
        if is_analytics:
            tables = compute_analytics_tables(state.bugs)
            render_inline_chart_and_table(q_norm, tables)

        col_a, col_b = st.columns(2)

        with col_a:
            with st.container(border=True):
                st.markdown("#### Evidence")
                if top_matches:
                    st.code(top_matches, language="text")
                else:
                    st.caption("No evidence available for this query.")

        with col_b:
            with st.container(border=True):
                st.markdown("#### Details")
                if other.strip():
                    st.code(other.strip(), language="text")
                else:
                    st.caption("No extra details.")

        with st.expander("Raw output"):
            st.code(out if out else "(no output)", language="text")
    
    # Preview dataset (use parsed bugs; avoids CSV parsing issues)
with st.expander("View demo dataset"):
    df_preview = pd.DataFrame(state.bugs)
    st.dataframe(df_preview, use_container_width=True)
    st.caption(f"Rows: {len(df_preview)} | Columns: {', '.join(df_preview.columns)}")
