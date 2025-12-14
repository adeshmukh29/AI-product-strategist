# src/llm_client.py
from typing import Optional
from openai import OpenAI
import json

from .agent_prompt import (
    STRATEGY_PIPELINE_SYSTEM_PROMPT,
    STRATEGY_PIPELINE_USER_TEMPLATE,
)


_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def run_llm(system_prompt: str, user_prompt: str, model: str = "gpt-4.1-mini") -> str:
    """
    Small helper to call the OpenAI Responses API and return plain text.
    """
    client = get_client()
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    # Try to be robust about how we pull text out
    try:
        return resp.output[0].content[0].text
    except Exception:
        # Some SDKs expose output_text directly
        return getattr(resp, "output_text", str(resp))
    
def generate_full_strategy_struct(
    *,
    product_name: str,
    target_users: str,
    goal: str,
    company_type: str,
    constraints: str,
    tavily_raw_json: str,
    extra_instructions: str = "",
    model: str = "gpt-5-nano",
) -> dict:
    """
    Calls the OpenAI Responses API and returns a full structured strategy JSON:
    - market_overview
    - competitor_analysis
    - user_pain_analysis
    - market_gaps
    - feature_ideas
    - prioritized_features (with scores)
    - three_month_roadmap
    - prds
    """
    client = get_client()

    user_prompt = STRATEGY_PIPELINE_USER_TEMPLATE.format(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints or "none specified",
        tavily_raw_json=tavily_raw_json,
        extra_instructions=extra_instructions or "None",
    )

    # ❗ NO response_format here – your SDK doesn’t support it
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": STRATEGY_PIPELINE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    # Try to safely get the JSON string from the response
    try:
        json_str = resp.output_text  # many SDKs expose this
    except Exception:
        try:
            json_str = resp.output[0].content[0].text
        except Exception:
            raise RuntimeError("Could not extract text from OpenAI response")

    # First attempt: parse directly
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Fallback: try to strip any leading/trailing noise
        start = json_str.find("{")
        end = json_str.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = json_str[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # If we reach here, the model didn't obey the JSON-only instruction
        raise ValueError(
            f"LLM returned invalid JSON for strategy pipeline. Raw text was:\n{json_str}"
        )


def render_strategy_markdown(strategy: dict) -> str:
    """
    Turn the strategy JSON into a human-readable markdown doc.
    """
    product_name = strategy.get("product_name", "")
    target_users = strategy.get("target_users", "")
    goal = strategy.get("goal", "")
    company_type = strategy.get("company_type", "")
    constraints = strategy.get("constraints", "")

    market_overview = strategy.get("market_overview", "")
    competitor_analysis = strategy.get("competitor_analysis", "")
    user_pain_analysis = strategy.get("user_pain_analysis", "")
    market_gaps = strategy.get("market_gaps", [])
    feature_ideas = strategy.get("feature_ideas", [])
    prioritized_features = strategy.get("prioritized_features", [])
    roadmap = strategy.get("three_month_roadmap", {})
    prds = strategy.get("prds", [])

    lines: list[str] = []

    lines.append(f"# AI Product Strategy – {product_name}\n")
    lines.append(f"**Target users:** {target_users}")
    lines.append(f"**Goal:** {goal}")
    lines.append(f"**Company type:** {company_type}")
    lines.append(f"**Constraints:** {constraints or 'None'}\n")

    lines.append("## 1. Market Overview\n")
    lines.append(market_overview or "_No overview generated._")
    lines.append("")

    lines.append("## 2. Competitor Analysis\n")
    lines.append(competitor_analysis or "_No competitor analysis._")
    lines.append("")

    lines.append("## 3. User Pain Analysis\n")
    lines.append(user_pain_analysis or "_No user pain analysis._")
    lines.append("")

    lines.append("## 4. Market Gaps\n")
    if market_gaps:
        for gap in market_gaps:
            lines.append(f"- {gap}")
    else:
        lines.append("_No gaps identified._")
    lines.append("")

    lines.append("## 5. Feature Ideas\n")
    if feature_ideas:
        for f in feature_ideas:
            lines.append(f"### {f.get('name', 'Unnamed feature')}")
            lines.append(f"{f.get('description', '')}")
            lines.append(f"- Solves gap: {f.get('solves_gap', '')}")
            lines.append(f"- Solves pain: {f.get('solves_pain', '')}")
            lines.append("")
    else:
        lines.append("_No feature ideas._")
    lines.append("")

    lines.append("## 6. Prioritized Features (with scores)\n")
    if prioritized_features:
        sorted_features = sorted(
            prioritized_features,
            key=lambda x: x.get("score", {}).get("overall_priority", 999),
        )
        for f in sorted_features:
            score = f.get("score", {})
            lines.append(f"### {f.get('name', 'Unnamed feature')}")
            lines.append(f"{f.get('description', '')}")
            lines.append(
                f"- Impact: {score.get('impact', '?')} / 5\n"
                f"- Complexity: {score.get('complexity', '?')} / 5\n"
                f"- Effort: {score.get('effort', '?')} / 5\n"
                f"- Overall priority: {score.get('overall_priority', '?')}"
            )
            lines.append("")
    else:
        lines.append("_No prioritized features._")
    lines.append("")

    lines.append("## 7. 3-Month Roadmap\n")
    lines.append("### Month 1")
    for item in roadmap.get("month_1", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### Month 2")
    for item in roadmap.get("month_2", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### Month 3")
    for item in roadmap.get("month_3", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## 8. PRDs (Product Requirement Documents)\n")
    if prds:
        for prd in prds:
            lines.append(f"### {prd.get('feature_name', 'Unnamed feature')}")
            lines.append(f"**Description:** {prd.get('description', '')}")
            lines.append(f"**Target users:** {', '.join(prd.get('target_users', []))}")
            lines.append(f"**Motivation:** {prd.get('motivation', '')}")
            lines.append("**Acceptance criteria:**")
            for ac in prd.get("acceptance_criteria", []):
                lines.append(f"- {ac}")
            lines.append("**Risks:**")
            for r in prd.get("risks", []):
                lines.append(f"- {r}")
            lines.append("")
    else:
        lines.append("_No PRDs generated._")

    return "\n".join(lines)
