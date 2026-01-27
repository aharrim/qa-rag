import os
from openai import OpenAI


def build_llm_context(results, max_chars=4000):
    # Chroma query() returns lists-of-lists for docs/metas/ids
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    ids = (results.get("ids") or [[]])[0]

    parts = []
    total = 0
    for bug_id, meta, doc in zip(ids, metas, docs):
        meta = meta or {}
        title = meta.get("title", "")
        severity = meta.get("severity", "")
        component = meta.get("component", "")
        block = (
            f"BUG_ID: {bug_id}\n"
            f"TITLE: {title}\n"
            f"SEVERITY: {severity}\n"
            f"COMPONENT: {component}\n"
            f"TEXT:\n{doc}\n"
        )
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)

    return "\n---\n".join(parts)


def ollama_generate(
    prompt: str,
    OLLAMA_URL: str | None = None,
    MODEL: str = "llama-3.1-8b-instant",
) -> str:
    """
    Backward-compatible function name.
    Uses Groq OpenAI-compatible endpoint under the hood.

    - OLLAMA_URL is ignored (kept only to avoid refactors).
    - MODEL is a Groq model id, e.g. 'llama-3.1-8b-instant'.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY env var")

    model = os.environ.get("GROQ_MODEL", MODEL)

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return resp.choices[0].message.content or ""








# import requests

# def build_llm_context(results, max_chars=4000):
#     docs = results["documents"][0]
#     metas = results["metadatas"][0]
#     ids  = results["ids"][0]

#     parts = []
#     total = 0
#     for bug_id, meta, doc in zip(ids, metas, docs):
#         title = meta.get("title", "")  # notebook does this (often empty)
#         severity = meta.get("severity", "")
#         component = meta.get("component", "")
#         block = f"BUG_ID: {bug_id}\nTITLE: {title}\nSEVERITY: {severity}\nCOMPONENT: {component}\nTEXT:\n{doc}\n"
#         if total + len(block) > max_chars:
#             break
#         parts.append(block)
#         total += len(block)
#     return "\n---\n".join(parts)


# def ollama_generate(prompt, OLLAMA_URL: str, MODEL: str):
#     payload = {
#         "model": MODEL,
#         "prompt": prompt,
#         "stream": False,
#         "temperature": 0.2
#     }
#     r = requests.post(OLLAMA_URL, json=payload, timeout=60)
#     r.raise_for_status()
#     return r.json()["response"]
