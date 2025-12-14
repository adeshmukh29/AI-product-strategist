# main.py — MCPApp for LastMile Cloud (no create_mcp_server_for_app)

import os
import json
from typing import Dict, Any

from openai import OpenAI
from mcp_agent.app import MCPApp

import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR  # main.py is already at project root
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.research_tools import research_bundle
from src.db import save_strategy_to_db, search_similar_strategies
from src.agent_prompt import SYSTEM_PROMPT
from src.llm_client import generate_full_strategy_struct, render_strategy_markdown

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
    extra_instructions: str = "",
) -> Dict[str, Any]:
    """
    End-to-end strategy workflow aligned with abstract:

    1. Run Tavily research (pains, competitors, trends).
    2. Call OpenAI to generate a FULL structured strategy:
       - market overview
       - competitor analysis
       - user pain analysis
       - market gaps
       - feature ideas
       - feature scoring & prioritization
       - 3-month roadmap
       - PRDs for top features
    3. Render markdown for human reading.
    4. Save full result into MongoDB with embeddings.
    5. Return research + structured strategy + markdown.
    """

    # 1) Tavily research via your existing helper
    research = research_bundle(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints,
    )

    tavily_raw_json = json.dumps(research["tavily_raw"], indent=2)

    # 2) Call LLM to generate full structured strategy JSON
    strategy_struct = generate_full_strategy_struct(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints or "none specified",
        tavily_raw_json=tavily_raw_json,
        extra_instructions=extra_instructions,
    )

    # 3) Render markdown for humans
    strategy_markdown = render_strategy_markdown(strategy_struct)

    # 4) Attach to the research payload
    research["strategy_json"] = strategy_struct
    research["strategy_markdown"] = strategy_markdown

   # 5) Save to MongoDB + embeddings (now includes strategy_json)
    mongo_status = {"status": "skipped"}
    try:
        mongo_status = save_strategy_to_db(research)
    except Exception as e:
        # Don’t crash the tool if Mongo is unreachable
        mongo_status = {"status": "error", "error": str(e)}

    # 6) Attach status and return everything
    research["mongo_save"] = mongo_status
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
