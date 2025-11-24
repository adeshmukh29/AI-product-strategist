# src/workflows.py
import json
import os
from typing import Any, Dict

from fastmcp import FastMCP
from openai import OpenAI
from src.db_client import save_strategy_run

from src.db import save_strategy_to_db


from .research_tools import build_research_bundle


app = FastMCP("strategy")


def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)


# @app.tool
# def strategy_pipeline(
#     product_name: str,
#     target_users: str,
#     goal: str,
#     company_type: str = "mid-size B2B SaaS",
#     constraints: str = "",
# ) -> Dict[str, Any]:
#     """
#     End-to-end workflow:
#     1) Run pains/competitors/trends research.
#     2) Feed results to OpenAI.
#     3) Return a structured strategy document + raw sources.
#     """
#     research = build_research_bundle(
#         product_name=product_name,
#         target_users=target_users,
#         goal=goal,
#         company_type=company_type,
#         constraints=constraints,
#     )


#     client = _get_openai_client()

#     prompt = f"""
# You are a senior AI Product Strategist.

# You are helping define the strategy for a product called:
# - Product: {product_name}
# - Target users: {target_users}
# - Company type: {company_type}
# - Goal: {goal}
# - Constraints: {constraints or "none specified"}

# You are given Tavily web research (JSON) with pains, competitors and trends:

# {json.dumps(research["tavily_raw"], indent=2)}

# Using this, write a clear strategy document in markdown with the following sections:

# 1. Market overview
# 2. Key competitors and what they do well / badly
# 3. User pain points and unmet needs
# 4. Suggested product positioning
# 5. 5–8 concrete feature ideas (with 1–2 lines of reasoning each)
# 6. Risks / assumptions
# 7. Next steps for validation (2–3 month plan, experiments + metrics)

# Make it concise, practical and specific to mid-size B2B SaaS. Use headings and bullet
# points where helpful.
# """

#     resp = client.responses.create(
#         model="gpt-5-nano",
#         input=prompt,
#     )


#     strategy_markdown = resp.output_text
#     research["strategy_markdown"] = strategy_markdown

#     # save to mongo
#     doc_id = save_strategy_run(research)

#     # remove MongoDB ObjectId to keep MCP safe
#     if "_id" in research:
#         research["_id"] = str(research["_id"])

#     # attach the inserted id
#     research["mongo_id"] = doc_id

#     return research
@app.tool
def strategy_pipeline(
    product_name: str,
    target_users: str,
    goal: str,
    company_type: str = "mid-size B2B SaaS",
    constraints: str = "",
) -> Dict[str, Any]:
    # 1) Run Tavily research bundle
    research = research_bundle(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints,
    )

    # 2) Call OpenAI to generate the strategy markdown
    client = _get_openai_client()

    prompt = f"""
You are a senior AI Product Strategist.

You are helping define the strategy for a product called:
- Product: {product_name}
- Target users: {target_users}
- Company type: {company_type}
- Goal: {goal}
- Constraints: {constraints or "none specified"}

You are given Tavily web research (JSON) with pains, competitors and trends:

{json.dumps(research["tavily_raw"], indent=2)}

Using this, write a clear strategy document in markdown with the following sections:

1. Market overview
2. Key competitors and what they do well / badly
3. User pain points and unmet needs
4. Suggested product positioning
5. 5–8 concrete feature ideas (with 1–2 lines of reasoning each)
6. Risks / assumptions
7. Next steps for validation (2–3 month plan, experiments + metrics)

Make it concise, practical and specific to mid-size B2B SaaS. Use headings and bullet
points where helpful.
"""

    resp = client.responses.create(
        model="gpt-5-nano",
        input=prompt,
    )

    strategy_markdown = resp.output_text
    research["strategy_markdown"] = strategy_markdown

    # 3) Save raw run (no embeddings) – goes to `strategy_runs`
    archive_id = save_strategy_run(research)

    # 4) Save embedded strategy (with vector) – goes to `strategies`
    vec_result = save_strategy_to_db(research)

    # 5) Add metadata for debugging / UI, but keep it safe
    research["mongo_archive_id"] = archive_id
    research["vector_saved"] = bool(vec_result.get("inserted"))

    return research


