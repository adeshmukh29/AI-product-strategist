# src/memory_tools.py
from fastmcp import FastMCP
from .db import save_strategy_to_db, search_similar_strategies

from bson import ObjectId
from .db_client import get_mongo_collection

app = FastMCP("memory")


@app.tool
def memory_save_strategy(strategy: dict) -> dict:
    """
    Save strategy into MongoDB with embedding.
    """
    return save_strategy_to_db(strategy)


@app.tool
def memory_search_similar(query: str, top_k: int = 3) -> dict:
    """
    Vector search strategies similar to query.
    """
    return {"results": search_similar_strategies(query, top_k)}



@app.tool
def memory_get_strategy_by_id(mongo_id: str) -> dict:
    """
    Return exactly one saved strategy by Mongo `_id`
    """
    coll = get_mongo_collection()
    doc = coll.find_one({"_id": ObjectId(mongo_id)})

    if not doc:
        return {"error": "Not found"}

    # Convert ObjectId → string
    doc["_id"] = str(doc["_id"])
    return doc

