import os
from typing import Any, Dict
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_mongo_client: MongoClient | None = None

def get_mongo_collection():
    global _mongo_client

    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB")
    coll_name = os.getenv("MONGODB_COLLECTION")

    if not uri or not db_name or not coll_name:
        raise RuntimeError("MongoDB env vars not set correctly")

    if _mongo_client is None:
        _mongo_client = MongoClient(uri)

    db = _mongo_client[db_name]
    return db[coll_name]


def save_strategy_run(payload: Dict[str, Any]) -> str:
    """
    Save one strategy result document and return the inserted ID.
    """
    coll = get_mongo_collection()
    result = coll.insert_one(payload)
    return str(result.inserted_id)
