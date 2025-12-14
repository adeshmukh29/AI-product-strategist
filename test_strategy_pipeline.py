import json

from src.research_tools import build_research_bundle
from src.llm_client import generate_full_strategy_struct, render_strategy_markdown
from src.db import save_strategy_to_db

def main():
    product_name = "AI onboarding assistant for SaaS products"
    target_users = "product managers at mid-size B2B SaaS companies"
    goal = "reduce time to onboard new users and increase activation"
    company_type = "mid-size B2B SaaS"
    constraints = "small team of 3 devs, need visible impact in 3 months"

    print("Running Tavily research...")
    research = build_research_bundle(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints,
    )

    tavily_raw_json = json.dumps(research["tavily_raw"], indent=2)

    print("Calling LLM for full strategy JSON...")
    strategy_struct = generate_full_strategy_struct(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints,
        tavily_raw_json=tavily_raw_json,
        extra_instructions="Focus on features that are low complexity but high impact.",
    )

    print("Strategy JSON keys:", strategy_struct.keys())

    print("Rendering markdown...")
    markdown = render_strategy_markdown(strategy_struct)

    # Attach to research payload exactly like strategy_run does
    research["strategy_json"] = strategy_struct
    research["strategy_markdown"] = markdown

    print("Saving to Mongo...")
    try:
        res = save_strategy_to_db(research)
        print("Mongo save result:", res)
    except Exception as e:
        print("⚠️ Could not save to MongoDB (dev env issue). Error:")
        print(e)


    # Just print first 40 lines of markdown
    print("\n--- Markdown preview (first 40 lines) ---")
    for i, line in enumerate(markdown.splitlines()):
        if i > 40:
            break
        print(line)

if __name__ == "__main__":
    main()
