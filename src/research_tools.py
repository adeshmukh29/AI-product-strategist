# src/research_tools.py
from typing import Any, Dict
from fastmcp import FastMCP

from .tavily_client import tavily_search

app = FastMCP("research")


# ---------- INTERNAL HELPERS (plain Python) ----------

def _research_pains_core(
    product_name: str,
    target_users: str,
    company_type: str = "mid-size B2B SaaS",
) -> Dict[str, Any]:
    query = (
        f"Top pain points and unmet needs for {target_users} "
        f"working on or using {product_name} in {company_type} context"
    )
    return tavily_search(
        query,
        topic="general",
        search_depth="basic",
        include_answer="basic",
        max_results=5,
    )


def _research_competitors_core(
    product_name: str,
    target_users: str,
    company_type: str = "mid-size B2B SaaS",
) -> Dict[str, Any]:
    query = (
        f"Key tools, platforms or competitors solving similar problems to "
        f"{product_name} for {target_users} in a {company_type} context"
    )
    return tavily_search(
        query,
        topic="general",
        search_depth="basic",
        include_answer="basic",
        max_results=5,
    )


def _research_trends_core(
    product_name: str,
    target_users: str,
    company_type: str = "mid-size B2B SaaS",
) -> Dict[str, Any]:
    query = (
        f"Recent trends, opportunities and risks in PM tooling / SaaS related to "
        f"{product_name} for {target_users} in {company_type}"
    )
    return tavily_search(
        query,
        topic="general",
        search_depth="basic",
        include_answer="basic",
        max_results=5,
    )


def build_research_bundle(
    product_name: str,
    target_users: str,
    goal: str,
    company_type: str = "mid-size B2B SaaS",
    constraints: str = "",
) -> Dict[str, Any]:
    """
    Plain Python function used by the workflow.
    """
    pains = _research_pains_core(product_name, target_users, company_type)
    competitors = _research_competitors_core(product_name, target_users, company_type)
    trends = _research_trends_core(product_name, target_users, company_type)

    tavily_queries = {
        "pains": pains["query"],
        "competitors": competitors["query"],
        "trends": trends["query"],
    }

    return {
        "product_name": product_name,
        "target_users": target_users,
        "goal": goal,
        "company_type": company_type,
        "constraints": constraints,
        "tavily_queries": tavily_queries,
        "tavily_raw": {
            "pains": pains,
            "competitors": competitors,
            "trends": trends,
        },
    }


# ---------- TOOL WRAPPERS (FastMCP) ----------

@app.tool
def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Generic Tavily web search.
    """
    return tavily_search(
        query,
        topic="general",
        search_depth="basic",
        include_answer="basic",
        max_results=max_results,
    )


@app.tool
def research_pains(
    product_name: str,
    target_users: str,
    company_type: str = "mid-size B2B SaaS",
) -> Dict[str, Any]:
    return _research_pains_core(product_name, target_users, company_type)


@app.tool
def research_competitors(
    product_name: str,
    target_users: str,
    company_type: str = "mid-size B2B SaaS",
) -> Dict[str, Any]:
    return _research_competitors_core(product_name, target_users, company_type)


@app.tool
def research_trends(
    product_name: str,
    target_users: str,
    company_type: str = "mid-size B2B SaaS",
) -> Dict[str, Any]:
    return _research_trends_core(product_name, target_users, company_type)


@app.tool
def research_bundle(
    product_name: str,
    target_users: str,
    goal: str,
    company_type: str = "mid-size B2B SaaS",
    constraints: str = "",
) -> Dict[str, Any]:
    """
    Tool version that just calls the plain helper.
    """
    return build_research_bundle(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints,
    )
