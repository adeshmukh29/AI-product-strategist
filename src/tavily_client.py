import os
from typing import Any, Dict, List, Optional
from tavily import TavilyClient

from dotenv import load_dotenv
load_dotenv()


_tavily_client: Optional[TavilyClient] = None


def get_tavily_client() -> TavilyClient:
    global _tavily_client
    if _tavily_client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY not set")
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


def tavily_search(
    query: str,
    *,
    topic: str = "general",
    search_depth: str = "basic",
    include_answer: bool | str = "basic",
    max_results: int = 5,
    time_range: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Thin wrapper over Tavily /search.
    """
    client = get_tavily_client()
    return client.search(
        query=query,
        topic=topic,
        search_depth=search_depth,
        include_answer=include_answer,
        max_results=max_results,
        time_range=time_range,
    )


def tavily_extract(
    urls: str | List[str],
    *,
    extract_depth: str = "basic",
    format: str = "markdown",
) -> Dict[str, Any]:
    client = get_tavily_client()
    return client.extract(
        urls=urls,
        extract_depth=extract_depth,
        format=format,
    )


def tavily_crawl(
    url: str,
    *,
    instructions: Optional[str] = None,
    max_depth: int = 1,
    limit: int = 50,
) -> Dict[str, Any]:
    client = get_tavily_client()
    return client.crawl(
        url=url,
        instructions=instructions,
        max_depth=max_depth,
        limit=limit,
    )
