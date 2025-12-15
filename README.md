```markdown
# AI Product Strategist (MCP + Tavily + MongoDB + UI)

An AI-powered product strategy generator that performs real-time web research, synthesizes a structured product strategy (and optional PRD/Roadmap), and saves results into MongoDB with vector embeddings for semantic search. Includes a Streamlit UI for a demo-friendly “business app” experience.

---

## 1) What the code does

This project turns a few high-level product inputs into a full strategy workflow:

- **Collects real-time web research** using **Tavily**:
  - user pain points
  - competitors
  - trends / opportunities / risks
- **Generates a strategy output** using **OpenAI (Responses API)**:
  - market overview
  - competitor analysis
  - user pain analysis
  - gaps/opportunities
  - feature ideas + prioritization
  - roadmap + PRD sections (if your pipeline produces them)
- **Stores outputs in MongoDB Atlas**:
  - stores the full run (raw + generated strategy)
  - creates an **embedding vector** (OpenAI embeddings) for the strategy text
  - enables **semantic similarity search** through MongoDB Vector Search
- **Provides tools / workflows**:
  - strategy pipeline tool (research → generate → save)
  - memory search tool (vector search over saved strategies)
  - research-only tool (Tavily only)
- **Provides a UI** (Streamlit) so non-technical users can generate strategies and follow-up refinements through a guided interface.

---

## 2) Project structure

A typical structure in this repo looks like:

```

ai-product-strategist/
├─ main.py
├─ ui.py                       # Streamlit UI (your demo UI entry)
├─ mcp_agent.config.yaml
├─ mcp_agent.secrets.yaml
├─ test_strategy_pipeline.py   # Local testing script
├─ src/
│  ├─ agent_prompt.py          # SYSTEM_PROMPT used for strategy generation
│  ├─ research_tools.py        # Tavily search tools + bundle builder
│  ├─ tavily_client.py         # Tavily client wrapper (search/extract/crawl)
│  ├─ llm_client.py            # OpenAI Responses API helper(s)
│  ├─ workflows.py             # strategy_pipeline workflow tool (FastMCP)
│  ├─ memory_tools.py          # memory save/search tools (FastMCP)
│  ├─ db.py                    # MongoDB save + embeddings + vector search
│  ├─ db_client.py             # Mongo connection + raw run archival
│  └─ (optional) vector_store.py
└─ .venv/                      # local virtual environment (not committed)

````

### Key files explained

- **`main.py`**
  - Entry point for the MCP app runtime.
  - Defines MCP tools like `strategy_run`, `research_only`, `memory_search_similar`.
  - Calls Tavily research + OpenAI strategy generation + MongoDB save.

- **`ui.py`**
  - Streamlit application to run the product as a “real UI”.
  - Collects user inputs and triggers the pipeline.
  - Displays strategy output and follow-up suggestions.

- **`src/research_tools.py`**
  - Implements Tavily-powered research primitives:
    - `research_pains`
    - `research_competitors`
    - `research_trends`
    - `research_bundle` (combined research output)
  - Also provides `web_search` helper.

- **`src/tavily_client.py`**
  - Tavily API wrapper:
    - `tavily_search`
    - `tavily_extract`
    - `tavily_crawl`

- **`src/agent_prompt.py`**
  - Contains your system prompt to keep outputs consistent and structured.

- **`src/llm_client.py`**
  - Helper to call OpenAI Responses API and return text / JSON.

- **`src/db.py`**
  - MongoDB integration:
    - embedding creation
    - insert strategy documents
    - vector search query pipeline

- **`src/db_client.py`**
  - Stores the raw run payload (useful for logging / audit).

- **`src/workflows.py`**
  - Defines the end-to-end pipeline tool (research → generate → save).
  - Useful for testing and/or MCP tool exposure.

---

## 3) How to prepare to run

### Prerequisites

- Windows / macOS / Linux
- Python installed (recommended: **Python 3.10–3.12**)
- API keys:
  - **OpenAI API key**
  - **Tavily API key**
  - **MongoDB Atlas connection string**

> Note: If you run Python 3.13 and some packages fail, switch to Python 3.11/3.12 for the smoothest setup.

---

### Step A — Create and activate a virtual environment (Windows)

From the project directory:

```bat
python -m venv .venv
.\.venv\Scripts\activate
````

You should see `(.venv)` in your terminal prompt.

---

### Step B — Install dependencies

Install core packages:

```bat
pip install -U pip
pip install openai pymongo python-dotenv tavily-python fastmcp mcp-agent streamlit
```

If Streamlit install times out, retry with:

```bat
pip install streamlit --timeout 300
```

---

### Step C — Create `.env` file

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here

MONGODB_URI=your_mongodb_atlas_uri_here
MONGODB_DB=ai_product_strategist
MONGODB_COLLECTION=strategy_runs
```

> Your code also uses a separate collection (ex: `strategies`) for vector-embedded docs inside `src/db.py`.
> Make sure you have that collection in Atlas (or let MongoDB create it on insert).

---

### Step D — MongoDB Vector Search setup (Atlas)

In MongoDB Atlas:

1. Create a database: `ai_product_strategist`
2. Create a collection: `strategies` (or match your code)
3. Create a Vector Search index (example name used in code: `vector_index`)

Example configuration (conceptual):

* **Index name:** `vector_index`
* **Path:** `vector`
* **Dimensions:** `3072` (for `text-embedding-3-large`)
* **Similarity:** `cosine`

> If you switch embedding models, update dimensions accordingly.

---

## 4) How to run

You have 3 typical run modes:

---

### Option 1 — Run the Streamlit UI (recommended for demos)

From project root (with venv activated):

```bat
streamlit run ui.py
```

Then open the Local URL shown in terminal (usually):

* `http://localhost:8501`

---

### Option 2 — Run a local pipeline test (CLI)

If you have `test_strategy_pipeline.py`:

```bat
python test_strategy_pipeline.py
```

This is useful to confirm:

* Tavily works
* OpenAI responses work
* MongoDB save works
* Embeddings + vector insert works

---


## Common troubleshooting

### Streamlit command not found

Make sure venv is active:

```bat
.\.venv\Scripts\activate
pip install streamlit
```


### MongoDB SSL / handshake errors

Common causes:

* IP not whitelisted in Atlas
* incorrect SRV connection string
* corporate network/VPN SSL interception

Fix checklist:

* Atlas → Network Access → add your IP (or temporarily allow `0.0.0.0/0` for testing)
* verify your `mongodb+srv://...` URI works in Atlas
* try from a different network

---

## Demo checklist (quick)

* Open Streamlit UI
* Enter inputs (product name, target users, goal, constraints)
* Click generate strategy
* Show:

  * Tavily research section (sources)
  * Strategy output (markdown)
  * MongoDB save confirmation
  * Similar strategy search (vector memory)

---

## License

Add your preferred license here (MIT / Apache-2.0 / etc.).

```
::contentReference[oaicite:0]{index=0}
```
