# import chromadb
# from chromadb.config import Settings
# from sentence_transformers import SentenceTransformer
# from typing import Any, cast
# from chromadb.utils import embedding_functions

# # matches your notebook exactly
# chroma_embedding = embedding_functions.SentenceTransformerEmbeddingFunction(
#     model_name="all-MiniLM-L6-v2"
# )

# embed_model = SentenceTransformer("all-MiniLM-L6-v2")


# def bug_to_text(bug: dict) -> str:
#     bug_id = bug["id"]
#     title = bug["title"]
#     component = bug["component"]
#     severity = bug["severity"]
#     created = bug["created_date"]
#     closed = bug["closed_date"] if bug["closed_date"] else "open"
#     details = bug["text"]

#     result = (
#         f"{bug_id} | {severity} | created : {created} | closed : {closed}\n"
#         f"Title : {title}\n"
#         f"Details : {details}"
#     )
#     return result


# def embed_texts(texts: list[str]) -> list[list[float]]:
#     vectors = embed_model.encode(texts, convert_to_numpy=True)
#     return vectors.tolist()


# def build_chroma_collection(bugs: list[dict], collection_name: str = "bugs"):
#     client = chromadb.PersistentClient(
#         path="./chroma_db_st",
#         settings=Settings(anonymized_telemetry=False)
#     )

#     collection = client.get_or_create_collection(
#         name=collection_name,
#         embedding_function=chroma_embedding
#     )

#     bug_ids = [b["id"] for b in bugs]
#     texts = [bug_to_text(bug) for bug in bugs]
#     embeddings = embed_texts(texts)

#     metadatas = [
#         {
#             "component": b["component"],
#             "severity": b["severity"],
#             "created_date": b["created_date"],
#             "closed_date": b["closed_date"] if b["closed_date"] is not None else "OPEN",
#             # NOTE: your notebook LLM context tries meta.get("title").
#             # You don't currently store it in metadata, so we keep it same (no title) to minimize changes.
#         }
#         for b in bugs
#     ]

#     embeddings = cast(Any, embeddings)
#     metadatas = cast(Any, metadatas)

#     collection.upsert(
#         ids=bug_ids,
#         documents=texts,
#         embeddings=embeddings,
#         metadatas=metadatas
#     )

#     return collection


import os
from pathlib import Path
from functools import lru_cache
from typing import Any, cast

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer


# Community Cloud + local friendly:
# - default to a repo-local folder (persistent across reruns; may reset on redeploy)
# - allow override via env var
CHROMA_PATH = Path(os.getenv("CHROMA_PATH", "./chroma_db_st"))
CHROMA_PATH.mkdir(parents=True, exist_ok=True)

# Optional: force rebuild collection (useful if CSV changed)
FORCE_REBUILD = os.getenv("CHROMA_FORCE_REBUILD", "0") == "1"


# Chroma can embed internally via its embedding function,
# but you ALSO want manual embeddings (because you upsert embeddings explicitly).
chroma_embedding = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


@lru_cache(maxsize=1)
def get_embed_model() -> SentenceTransformer:
    # Cached at process-level so it doesn't reload repeatedly
    return SentenceTransformer("all-MiniLM-L6-v2")


def bug_to_text(bug: dict) -> str:
    bug_id = bug.get("id")
    title = bug.get("title", "")
    component = bug.get("component", "")
    severity = bug.get("severity", "")
    created = bug.get("created_date", "")
    closed = bug.get("closed_date") if bug.get("closed_date") else "open"
    details = bug.get("text", "")

    return (
        f"{bug_id} | {severity} | component : {component} | created : {created} | closed : {closed}\n"
        f"Title : {title}\n"
        f"Details : {details}"
    )


def build_chroma_collection(bugs: list[dict], collection_name: str = "bugs"):
    """
    Builds (or reuses) a persistent Chroma collection and upserts bugs once.
    Safe for Streamlit: if collection already has docs, it returns immediately.

    Set env CHROMA_FORCE_REBUILD=1 to rebuild collection from scratch.
    """
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )

    if FORCE_REBUILD:
        # delete if exists, then recreate
        try:
            client.delete_collection(name=collection_name)
        except Exception:
            pass  # collection might not exist yet

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=chroma_embedding,
    )

    # Don't rebuild if already populated
    if not FORCE_REBUILD and collection.count() > 0:
        return collection

    # If rebuild was requested, we recreated collection above, so count should be 0.
    bug_ids = [str(b["id"]) for b in bugs]  # enforce string ids
    texts = [bug_to_text(b) for b in bugs]

    embed_model = get_embed_model()
    embeddings = embed_model.encode(texts, convert_to_numpy=True).tolist()

    metadatas = [
        {
            "component": b.get("component", ""),
            "severity": b.get("severity", ""),
            "created_date": b.get("created_date", ""),
            "closed_date": b.get("closed_date") if b.get("closed_date") is not None else "OPEN",
            "title": b.get("title", ""),  # helpful for UI/source display
        }
        for b in bugs
    ]

    collection.upsert(
        ids=cast(Any, bug_ids),
        documents=cast(Any, texts),
        embeddings=cast(Any, embeddings),
        metadatas=cast(Any, metadatas),
    )
    return collection
