import os

from .state import ProjectState
from .data import load_bugs_from_csv
from .analytics import bugs_to_df, analytics_reports
from .chroma_store import build_chroma_collection
from .llm import build_llm_context, ollama_generate
from .grounding import retrieval_is_weak, validate_llm_answer, format_safe_refusal
from .router import rule_route, analytics_dispatch


def build_state_from_csv_or_memory(
    bugs_in_memory: list[dict],
    CSV_PATH: str = "bugs_sample_20.csv",
    collection_name: str = "bugs",
    OLLAMA_URL: str = "http://localhost:11434/api/generate",
    #MODEL: str = "qwen2.5",
    MODEL: str = "llama-3.1-8b-instant",
) -> ProjectState:

    bugs = bugs_in_memory
    if os.path.exists(CSV_PATH):
        bugs = load_bugs_from_csv(CSV_PATH)

    df = bugs_to_df(bugs)
    open_by_component, resolution_by_component, open_critical, open_critical_by_component = analytics_reports(df)

    collection = build_chroma_collection(bugs, collection_name=collection_name)

    return ProjectState(
        bugs=bugs,
        df=df,
        open_by_component=open_by_component,
        resolution_by_component=resolution_by_component,
        open_critical=open_critical,
        open_critical_by_component=open_critical_by_component,
        collection=collection,
        OLLAMA_URL=OLLAMA_URL,
        MODEL=MODEL,
    )


def answer_question(state: ProjectState, user_question: str, top_k: int = 3, max_dist_threshold: float = 0.55):
    route = rule_route(user_question)
    if route is None:
        # keep your behavior: default to ANALYTICS? (you defaulted to LLM route)
        # We'll default to RAG if unclear — safer.
        route = "RAG"

    print(f"\n[Router] Route = {route}\n")

    if route == "ANALYTICS":
        analytics_dispatch(
            user_question=user_question,
            df=state.df,
            open_by_component=state.open_by_component,
            resolution_by_component=state.resolution_by_component,
            open_critical=state.open_critical,
            open_critical_by_component=state.open_critical_by_component,
        )
        return

    # --- RAG route ---
    rag_query = user_question
    rag_results = state.collection.query(
        query_texts=[rag_query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    print("=== RAG Top Matches ===")
    for i in range(len(rag_results["ids"][0])):
        bug_id = rag_results["ids"][0][i]
        meta = rag_results["metadatas"][0][i]
        dist = rag_results["distances"][0][i]
        doc_preview = rag_results["documents"][0][i][:160].replace("\n", " ")
        print(f"{i+1}) {bug_id} | {meta.get('severity')} | {meta.get('component')} | {meta.get('closed_date')} | dist={dist:.4f}")
        print("   ", doc_preview, "...\n")

    # Grounding: weak retrieval → refusal
    if retrieval_is_weak(rag_results, max_dist_threshold=max_dist_threshold):
        print("=== Final Answer (Safe Refusal) ===")
        print(format_safe_refusal(rag_query, rag_results))
        return

    context = build_llm_context(rag_results)

    prompt = f"""
You are a QA assistant.
Answer the user's question using ONLY the bug context below.
If context is insufficient, say: "Not enough evidence in retrieved bugs."

USER QUESTION:
{rag_query}

BUG CONTEXT:
{context}

Return:
1) Short answer (2-4 lines)
2) List the bug IDs you used
""".strip()

    llm_answer = ollama_generate(prompt, OLLAMA_URL=state.OLLAMA_URL, MODEL=state.MODEL)

    ok, reason, used_ids = validate_llm_answer(llm_answer, rag_results, min_ids=1)
    if not ok:
        # (Optional debug) print(f"[Debug] Validation failed: {reason}")
        print("=== Final Answer (Safe Refusal) ===")
        print(format_safe_refusal(rag_query, rag_results))
        return

    print("=== Final Answer (Grounded) ===")
    print(llm_answer.strip())
    print("\nEvidence bug IDs:", ", ".join(used_ids))
