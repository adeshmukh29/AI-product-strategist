# ui.py – Business-style Streamlit UI for AI Product Strategist

import os
import sys
import json
import textwrap
from datetime import datetime

import streamlit as st

# -------------------------------------------------------------------
# Make sure we can import from src/
# -------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.research_tools import build_research_bundle
from src.llm_client import generate_full_strategy_struct, render_strategy_markdown
from src.db import save_strategy_to_db, search_similar_strategies


# -------------------------------------------------------------------
# Strategy pipeline wrapper
# -------------------------------------------------------------------
def run_full_strategy_pipeline(
    product_name: str,
    target_users: str,
    goal: str,
    company_type: str,
    constraints: str,
    extra_instructions: str = "",
):
    # 1) Tavily research
    research = build_research_bundle(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints,
    )

    tavily_raw_json = json.dumps(research["tavily_raw"], indent=2)

    # 2) LLM → full structured strategy JSON
    strategy_struct = generate_full_strategy_struct(
        product_name=product_name,
        target_users=target_users,
        goal=goal,
        company_type=company_type,
        constraints=constraints or "none specified",
        tavily_raw_json=tavily_raw_json,
        extra_instructions=extra_instructions or "",
    )

    # 3) Render markdown for human-readable view
    strategy_markdown = render_strategy_markdown(strategy_struct)

    # 4) Attach to research payload
    research["strategy_json"] = strategy_struct
    research["strategy_markdown"] = strategy_markdown

    # 5) Save to Mongo, but don't crash UI if it fails
    mongo_status = {"status": "skipped"}
    try:
        mongo_status = save_strategy_to_db(research)
    except Exception as e:
        mongo_status = {"status": "error", "error": str(e)}

    research["mongo_save"] = mongo_status

    # 6) Add timestamp for in-app “history”
    research["created_at"] = datetime.utcnow().isoformat()

    return research


# -------------------------------------------------------------------
# Streamlit config
# -------------------------------------------------------------------
st.set_page_config(
    page_title="AI Product Strategist – Strategy Studio",
    page_icon="🧠",
    layout="wide",
)
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

# Simple session history (current session only)
if "runs" not in st.session_state:
    st.session_state["runs"] = []  # list of dicts


# -------------------------------------------------------------------
# Sidebar – navigation & brand
# -------------------------------------------------------------------
st.sidebar.markdown("### 🧠 AI Product Strategist")
st.sidebar.caption("Strategy Studio · Research Assistant · Vector Memory")

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Strategy Studio", "Memory Search"],
    index=1,   # default landing
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Built by Atharva Deshmukh**")
st.sidebar.caption("Real-time research · Strategy engine · Vector memory")




# -------------------------------------------------------------------
# HOME PAGE – “Landing page” style
# -------------------------------------------------------------------
if page == "Home":
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("#### Product Strategy, in Minutes – Not Weeks")
        st.markdown(
            """
            **AI Product Strategist** is your copilot for:

            - Deep market & competitor research (powered by Tavily)
            - Structured strategy docs (gaps, features, roadmap, PRDs)
            - Persistent knowledge (MongoDB + vector search)

            Instead of staring at a blank PRD or deck, you give the app:
            **a product idea, target users, and a goal** — it returns a
            full strategy you can refine and share.

            This is the kind of tool PMs, founders, and early-stage teams
            would pay for:
            - Faster discovery
            - Clear decision frameworks
            - Re-usable institutional memory
            """
        )

    with col_right:
        st.markdown("##### Quick Metrics (demo)")
        st.metric("Strategies this session", len(st.session_state["runs"]))
        st.metric("Average roadmap horizon", "3 months")
        st.metric("Typical PM time saved", "~4–6 hours / strategy")

        st.markdown("---")
        st.markdown("Want to try it right now?")
        if st.button("Go to Strategy Studio ➜"):
            st.info("Use the navigation on the left to open **Strategy Studio**.")



    st.markdown("---")
    st.markdown("#### Recent Strategies (this session)")
    if not st.session_state["runs"]:
        st.info("No strategies generated yet. Go to **Strategy Studio** to create one.")
    else:
        for i, r in enumerate(reversed(st.session_state["runs"]), start=1):
            strategy_json = r.get("strategy_json", {})
            created_at = r.get("created_at", "")
            product_name = strategy_json.get("product_name") or r.get("product_name", "Untitled product")
            goal = strategy_json.get("goal") or r.get("goal", "")

            with st.expander(f"{i}. {product_name} – {goal[:80]}"):
                st.write("**Created at (UTC):**", created_at)
                st.write("**Target users:**", strategy_json.get("target_users", "—"))
                st.write("**Company type:**", strategy_json.get("company_type", "—"))
                st.markdown("**Short summary:**")
                st.markdown(r.get("strategy_markdown", "")[:700] + " ...")


# -------------------------------------------------------------------
# STRATEGY STUDIO – main “business app” screen
# -------------------------------------------------------------------
elif page == "Strategy Studio":
    st.markdown("### 🧪 Strategy Studio")
    st.caption("Generate AI-backed product strategies, PRDs, and roadmaps from one place.")

    # Layout: inputs on the right, explanation on the left
    col_explain, col_form = st.columns([1.2, 1])

    with col_explain:
        st.markdown(
            """
            **How it works:**

            1. Fill in the product, target users, and high-level goal.
            2. The app runs **Tavily research** on pains, competitors, and trends.
            3. A structured **strategy JSON** is generated:
               - Market overview & gaps
               - Feature ideas with scoring
               - 3-month roadmap
               - PRDs for the top features
            4. Everything is saved into **MongoDB with embeddings** for later retrieval.

            This is kind of workflow can be used as:
            - A PM research assistant
            - A startup strategy generator
            - A consulting “pre-work” accelerator
            """
        )

    with col_form:
        st.markdown("#### Strategy Inputs")

        default_product = "AI onboarding assistant for SaaS"
        default_users = "Product managers at mid-size B2B SaaS companies"
        default_goal = "Reduce time-to-value and increase user activation during onboarding."

        product_name = st.text_input("Product name", value=default_product)
        target_users = st.text_area("Target users", value=default_users, height=70)
        goal = st.text_area("Primary goal", value=default_goal, height=70)

        company_type = st.text_input("Company type", value="mid-size B2B SaaS")

        constraints = st.text_area(
            "Constraints (team, time, budget...)",
            value="Team of 3 devs, 3-month runway, limited design resources.",
            height=60,
        )

        extra_instructions = st.text_area(
            "Extra instructions (optional)",
            value="Prioritize low-effort, high-impact features and self-serve onboarding.",
            height=60,
        )

        run_button = st.button("🚀 Generate Strategy", type="primary")

    # Place where results will render
    st.markdown("---")

    if run_button:
        if not product_name.strip() or not target_users.strip() or not goal.strip():
            st.error("Please fill in Product name, Target users, and Goal.")
        else:
            with st.spinner("Running Tavily research and generating full strategy..."):
                try:
                    result = run_full_strategy_pipeline(
                        product_name=product_name,
                        target_users=target_users,
                        goal=goal,
                        company_type=company_type,
                        constraints=constraints,
                        extra_instructions=extra_instructions,
                    )
                except Exception as e:
                    st.error(f"Something went wrong while generating the strategy: {e}")
                    result = None

            if result:
                # Save to session history
                st.session_state["runs"].append(result)

                strategy_json = result.get("strategy_json", {})
                strategy_markdown = result.get("strategy_markdown", "")
                tavily_raw = result.get("tavily_raw", {})
                mongo_status = result.get("mongo_save", {})

                # Summary strip
                st.success("Strategy generated successfully.")
                meta_col1, meta_col2, meta_col3 = st.columns(3)
                with meta_col1:
                    st.metric("Product", strategy_json.get("product_name", "—"))
                with meta_col2:
                    st.metric("Target users", "Defined")
                with meta_col3:
                    st.metric("Mongo save status", mongo_status.get("status", "unknown"))

                # Tabs: overview, research, JSON, PRDs, roadmap, memory
                tab_overview, tab_research, tab_json, tab_prds, tab_roadmap, tab_memory = st.tabs(
                    [
                        "📄 Strategy overview",
                        "🔎 Research (Tavily)",
                        "🧱 Strategy JSON",
                        "📑 PRDs",
                        "🗺️ 3-month roadmap",
                        "🧠 Vector memory",
                    ]
                )

                # 1) Overview
                with tab_overview:
                    st.subheader("Strategy overview")
                    st.markdown(strategy_markdown)

                # 2) Research
                with tab_research:
                    st.subheader("Tavily research – pains / competitors / trends")

                    pains = tavily_raw.get("pains", {})
                    competitors = tavily_raw.get("competitors", {})
                    trends = tavily_raw.get("trends", {})

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("##### Pain points")
                        if pains:
                            st.write("**Query:**", pains.get("query"))
                            st.json(pains.get("results", []))
                        else:
                            st.info("No pains data.")

                    with col2:
                        st.markdown("##### Competitors")
                        if competitors:
                            st.write("**Query:**", competitors.get("query"))
                            st.json(competitors.get("results", []))
                        else:
                            st.info("No competitor data.")

                    with col3:
                        st.markdown("##### Trends")
                        if trends:
                            st.write("**Query:**", trends.get("query"))
                            st.json(trends.get("results", []))
                        else:
                            st.info("No trend data.")

                # 3) Raw JSON
                with tab_json:
                    st.subheader("Full strategy JSON (matches abstract)")
                    st.json(strategy_json)

                # 4) PRDs
                with tab_prds:
                    st.subheader("PRDs for top features")

                    prds = strategy_json.get("prds", [])
                    if not prds:
                        st.info("No PRDs found in JSON.")
                    else:
                        for i, prd in enumerate(prds, start=1):
                            title = prd.get("title", f"Feature {i}")
                            with st.expander(f"PRD #{i}: {title}"):
                                st.write("**Feature title:**", title)
                                st.write("**Description:**", prd.get("description", "—"))
                                st.write("**Target users:**", prd.get("target_users", "—"))
                                st.write("**Motivation:**", prd.get("motivation", "—"))
                                st.write("**Acceptance criteria:**")
                                ac = prd.get("acceptance_criteria", [])
                                if isinstance(ac, list):
                                    for item in ac:
                                        st.markdown(f"- {item}")
                                else:
                                    st.write(ac or "—")
                                st.write("**Risks / assumptions:**", prd.get("risks", "—"))

                # 5) Roadmap
                with tab_roadmap:
                    st.subheader("3-month roadmap")

                    roadmap = strategy_json.get("three_month_roadmap", {})
                    if not roadmap:
                        st.info("No roadmap found in JSON.")
                    else:
                        for key in ["month_1", "month_2", "month_3"]:
                            if key in roadmap:
                                st.markdown(f"#### {key.replace('_', ' ').title()}")
                                st.write(roadmap[key])

                # 6) Vector memory
                with tab_memory:
                    st.subheader("Vector memory – semantic search")
                    st.write("MongoDB save status:", mongo_status)

                    st.markdown(
                        textwrap.dedent(
                            """
                            Use this section to search for **similar strategies** based on meaning
                            using MongoDB Atlas Vector Search.
                            """
                        )
                    )

                    query = st.text_input(
                        "Search query (e.g., 'AI onboarding for SaaS', 'pricing assistant')",
                        value=f"Similar to {product_name}",
                    )
                    top_k = st.slider("Number of matches", 1, 10, 3)

                    if st.button("🔎 Search similar strategies"):
                        try:
                            results = search_similar_strategies(query, top_k=top_k)
                        except Exception as e:
                            st.error(f"Error during vector search: {e}")
                        else:
                            if not results:
                                st.info("No similar strategies found.")
                            else:
                                for idx, r in enumerate(results, start=1):
                                    with st.expander(
                                        f"Result #{idx} – {r.get('product_name', 'Unknown product')} "
                                        f"(score: {round(r.get('score', 0), 3)})"
                                    ):
                                        st.markdown(r.get("strategy_markdown", "No markdown stored."))


# -------------------------------------------------------------------
# MEMORY SEARCH – separate page, “business-y” feel
# -------------------------------------------------------------------
elif page == "Memory Search":
    st.markdown("### 🧠 Strategy Memory Search")
    st.caption(
        "Explore strategies saved to MongoDB using semantic vector search. "
        "In a real SaaS, this becomes your organization's product knowledge base."
    )

    query = st.text_input(
        "Search phrase",
        value="AI onboarding assistant",
        help="Describe the type of strategy you’re looking for.",
    )
    top_k = st.slider("Number of results", 1, 10, 5)

    if st.button("Run memory search"):
        with st.spinner("Searching vector memory..."):
            try:
                results = search_similar_strategies(query, top_k=top_k)
            except Exception as e:
                st.error(f"Error during vector search: {e}")
            else:
                if not results:
                    st.info("No results found. Try a broader query.")
                else:
                    for idx, r in enumerate(results, start=1):
                        with st.expander(
                            f"Result #{idx} – {r.get('product_name', 'Unknown product')} "
                            f"(score: {round(r.get('score', 0), 3)})"
                        ):
                            st.markdown(r.get("strategy_markdown", "No markdown stored."))
