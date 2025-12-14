# src/db.py
import os
from pymongo import MongoClient
from openai import OpenAI
import numpy as np

def get_mongo_client():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI not set in .env")
    return MongoClient(uri)

def get_openai():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing")
    return OpenAI(api_key=key)

# ---- VECTOR ENCODER ----
def embed_text(text: str) -> list:
    client = get_openai()
    resp = client.embeddings.create(
        model="text-embedding-3-large",
        input=text,
    )
    return resp.data[0].embedding

# ---- SAVE STRATEGY ----
def save_strategy_to_db(strategy: dict):
    client = get_mongo_client()
    db = client["ai_product_strategist"]
    col = db["strategies"]

    text = strategy.get("strategy_markdown", "")
    vector = embed_text(text)

    doc = {
        "product_name": strategy.get("product_name"),
        "target_users": strategy.get("target_users"),
        "goal": strategy.get("goal"),
        "company_type": strategy.get("company_type"),
        "constraints": strategy.get("constraints"),
        "strategy_markdown": text,
        "vector": vector,
        "tavily_raw": strategy.get("tavily_raw"),
        # NEW: store the structured strategy JSON if provided
        "strategy_json": strategy.get("strategy_json"),
    }

    col.insert_one(doc)
    return {"status": "ok", "inserted": True}


# ---- VECTOR SEARCH ----
# def search_similar_strategies(query: str, top_k: int = 3):
#     client = get_mongo_client()
#     db = client["ai_product_strategist"]
#     col = db["strategies"]

#     query_vec = embed_text(query)

#     results = col.aggregate([
#         {
#             "$vectorSearch": {
#                 "queryVector": query_vec,
#                 "path": "vector",
#                 "numCandidates": 50,
#                 "limit": top_k,
#                 "index": "vector_index"
#             }
#         },
#         {
#             "$project": {
#                 "product_name": 1,
#                 "score": {"$meta": "vectorSearchScore"},
#                 "strategy_markdown": 1
#             }
#         }
#     ])

#     for r in results:
#         if "_id" in r:
#             r["_id"] = str(r["_id"])

#     return results
def search_similar_strategies(query: str, top_k: int = 3):
    client = get_mongo_client()
    db = client["ai_product_strategist"]
    col = db["strategies"]

    query_vec = embed_text(query)

    results = col.aggregate([
        {
            "$vectorSearch": {
                "queryVector": query_vec,
                "path": "vector",
                "numCandidates": 50,
                "limit": top_k,
                "index": "vector_index"
            }
        },
        {
            "$project": {
                "_id": 0,  # important so we don't return ObjectId
                "product_name": 1,
                "score": { "$meta": "vectorSearchScore" },
                "strategy_markdown": 1,
            }
        }
    ])

    return list(results)

