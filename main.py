# main.py — MCPApp for LastMile Cloud (no create_mcp_server_for_app)

import os
import json
from typing import Dict, Any

from openai import OpenAI
from mcp_agent.app import MCPApp

from src.research_tools import research_bundle
from src.db import save_strategy_to_db, search_similar_strategies
from src.agent_prompt import SYSTEM_PROMPT

# ---------------------------------------------------------------------
# Define the MCPApp that Cloud will load
# ---------------------------------------------------------------------

app = MCPApp(name="ai-product-strategist")


def _get_openai_client() -> OpenAI:
    """
    Use OPENAI_API_KEY from env (LastMile will inject it from secrets).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return OpenAI(api_key=api_key)
    return OpenAI()


# ---------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------

@app.tool
async def strategy_run(
    product_name: str,
    target_users: str,
    goal: str,
    company_type: str = "mid-size B2B SaaS",
    constraints: str = "",
) -> Dict[str, Any]:
    """
    End-to-end strategy workflow:

    1. Run Tavily research (pains, competitors, trends).
    2. Call OpenAI to synthesize a strategy document in markdown.
    3. Save full result into MongoDB with embeddings.
    4. Return the full JSON (research + strategy_markdown).
    """

    # 1) Tavily research via your existing helper
    research = research_bundle(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints,
    )

    client = _get_openai_client()
    tavily_raw_json = json.dumps(research["tavily_raw"], indent=2)

    prompt = f"""
{SYSTEM_PROMPT}

You are helping define the strategy for a product with the following context:

- Product: {product_name}
- Target users: {target_users}
- Company type: {company_type}
- Goal: {goal}
- Constraints: {constraints or "none specified"}

You are given Tavily web research (JSON) with pains, competitors and trends:

{tavily_raw_json}

Using this, write a clear strategy document in markdown with the following sections:

1. Market overview
2. Key competitors and what they do well / badly
3. User pain points and unmet needs
4. Suggested product positioning
5. 5–8 concrete feature ideas (with 1–2 lines of reasoning each)
6. Risks / assumptions
7. Next steps for validation (2–3 month plan, experiments + metrics)

Make it concise, practical and specific to mid-size B2B SaaS.
Use headings and bullet points where helpful.
"""

    resp = client.responses.create(
        model="gpt-5-nano",
        input=prompt,
    )

    try:
        strategy_markdown = resp.output_text
    except Exception:
        try:
            strategy_markdown = resp.output[0].content[0].text
        except Exception:
            strategy_markdown = str(resp)

    research["strategy_markdown"] = strategy_markdown

    # Save to MongoDB + embeddings
    save_strategy_to_db(research)

    return research


@app.tool
async def memory_search_similar(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Semantic search over previously saved strategies
    using MongoDB Atlas Vector Search.
    """
    results = search_similar_strategies(query, top_k)
    return {"results": results}


@app.tool
async def research_only(
    product_name: str,
    target_users: str,
    goal: str,
    company_type: str = "mid-size B2B SaaS",
    constraints: str = "",
) -> Dict[str, Any]:
    """
    Run only the Tavily research bundle without synthesizing a strategy.
    """
    return research_bundle(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints,
    )

# ⬅️ IMPORTANT:
# No `if __name__ == "__main__":` block here.
# Cloud only needs the `app` object defined above.
