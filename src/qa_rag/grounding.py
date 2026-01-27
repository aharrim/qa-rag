import re

BUG_ID_RE = r"\bBUG-\d+\b"

def retrieval_is_weak(rag_results, max_dist_threshold=0.55) -> bool:
    try:
        dists = rag_results.get("distances", [[]])[0]
        if not dists:
            return True
        best = min(dists)
        return best > max_dist_threshold
    except Exception:
        return True


def validate_llm_answer(llm_answer: str, rag_results, min_ids: int = 1):
    retrieved_ids = set(rag_results.get("ids", [[]])[0])
    used_ids = sorted(set(re.findall(BUG_ID_RE, llm_answer or "")))

    if len(used_ids) < min_ids:
        return (False, "LLM did not cite any bug IDs.", used_ids)

    hallucinated = [bid for bid in used_ids if bid not in retrieved_ids]
    if hallucinated:
        return (False, f"LLM cited bug IDs not in retrieved context: {hallucinated}", used_ids)

    return (True, "OK", used_ids)


def format_safe_refusal(rag_query: str, rag_results) -> str:
    retrieved = rag_results.get("ids", [[]])[0]
    if not retrieved:
        return f"Not enough evidence in retrieved bugs for: '{rag_query}'. (No matches returned.)"

    top = retrieved[:3]
    return (
        f"Not enough evidence in retrieved bugs for: '{rag_query}'.\n"
        f"Closest matches found: {', '.join(top)}.\n"
        "Try rephrasing with more details (platform, screen, steps, error message)."
    )
