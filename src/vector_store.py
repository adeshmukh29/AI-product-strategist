import os
from typing import List, Dict, Any
from pymongo import MongoClient
from openai import OpenAI

_client = None
_db = None
_collection = None
_embed_client = None


def _get_collection():
    global _client, _db, _collection
    if _collection is None:
        uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB", "ai_product_strategist")
        coll_name = os.getenv("MONGODB_COLLECTION", "research")

        if not uri:
            raise RuntimeError("MONGODB_URI not set")

        _client = MongoClient(uri)
        _db = _client[db_name]
        _collection = _db[coll_name]
    return _collection


def _get_embed_client() -> OpenAI:
    global _embed_client
    if _embed_client is None:
        _embed_client = OpenAI()
    return _embed_client


def embed_text(texts: List[str]) -> List[List[float]]:
    """
    Uses OpenAI embeddings; change model if needed.
    """
    client = _get_embed_client()
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [d.embedding for d in resp.data]


def add_documents(
    docs: List[Dict[str, Any]],
    *,
    product: str,
    topic: str,
    source_urls: List[str],
):
    """
    Each doc: {"text": "...", "metadata": {...}}
    """
    coll = _get_collection()
    texts = [d["text"] for d in docs]
    vectors = embed_text(texts)

    to_insert = []
    for d, vec in zip(docs, vectors):
        base_meta = {
            "product": product,
            "topic": topic,
            "source_urls": source_urls,
        }
        base_meta.update(d.get("metadata", {}))
        to_insert.append(
            {
                "text": d["text"],
                "embedding": vec,
                "metadata": base_meta,
            }
        )
    if to_insert:
        coll.insert_many(to_insert)


def search_similar(
    query: str,
    *,
    k: int = 5,
    product: str | None = None,
    topic: str | None = None,
) -> List[Dict[str, Any]]:
    coll = _get_collection()
    [query_vec] = embed_text([query])

    filter_query: Dict[str, Any] = {}
    if product:
        filter_query["metadata.product"] = product
    if topic:
        filter_query["metadata.topic"] = topic

    # You'll need to set up a vector index in Atlas and update this
    # to use $vectorSearch or similar, but this is the conceptual structure.
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vec,
                "numCandidates": 50,
                "limit": k,
                "filter": filter_query or None,
            }
        },
        {
            "$project": {
                "_id": 0,
                "score": {"$meta": "vectorSearchScore"},
                "text": 1,
                "metadata": 1,
            }
        },
    ]
    docs = list(coll.aggregate(pipeline))

    for d in docs:
        if "_id" in d:
            d["_id"] = str(d["_id"])

    return docs

