# PartSelect AI Chat Agent — Instalily Case Study

With a focus on improving **user experience** and the **extensibility** of the solution, this project implements a multi-agent AI chat system for the PartSelect e-commerce platform, specializing in refrigerator and dishwasher parts. The architecture is designed to be modular, observable, and extensible — reflecting how Instalily thinks about building vertical AI agents for the physical economy.

---

## Problem Statement

PartSelect serves a wide range of customers — from DIY homeowners to professional field technicians — with a large, complex parts catalog. The core challenges:

- **Product discovery is hard**: Users don't always know the exact part number; they describe symptoms or appliance models.
- **Compatibility is non-trivial**: A part may fit some models but not others, and getting this wrong is costly.
- **Troubleshooting requires expertise**: Diagnosing an appliance issue and mapping it to the right part requires domain knowledge.
- **B2B ordering needs authentication**: Enterprise technicians need account-aware ordering, not anonymous checkouts.
- **Scope must be enforced**: A general-purpose chatbot on a parts website wastes user time and erodes trust.

---

## Solution: Multi-Agent Orchestration with LangGraph

The system uses a **supervisor-router + specialist agent** pattern built with LangGraph. The supervisor classifies intent and routes to the right agent - ensuring focused, accurate responses.

### Agents

| Agent | Responsibility |
|---|---|
| **Supervisor** | Classifies intent (`product`, `compatibility`, `troubleshoot`, `order`, `guard`) and routes the conversation |
| **Product Agent** | Finds parts by keyword, symptom query, or exact part number using semantic search over the catalog |
| **Compatibility Agent** | Checks whether a specific part fits a specific appliance model |
| **Troubleshoot Agent** | Diagnoses appliance symptoms and recommends the most likely replacement parts |
| **Order Agent** | Handles cart, order history, account lookup, and estimated delivery — B2B aware |
| **Recommendation Agent** | Triggers automatically when retrieved parts are low in stock — surfaces reorder urgency |
| **Guard Node** | Blocks off-topic queries and redirects cleanly |

### Custom Knowledge Base — Inspired by InstaBrain

A core part of the architecture is a **custom ChromaDB vector database** built from PartSelect's parts catalog, seeded with company-specific inventory data (parts, pricing, stock levels, compatibility, warehouse locations). This mirrors Instalily's InstaBrain model — a domain-specific knowledge store trained on a company's own data, rather than relying on a general-purpose LLM to hallucinate product details. Agents query this database semantically (e.g. "ice maker not working Whirlpool") and get back grounded, accurate results from the company's actual inventory. The seed pipeline (`seed_data.py` → `seed_chroma.py`) makes it easy to swap in a real catalog without changing any agent logic.

### Key Design Choices

- **Deterministic routing**: The supervisor uses structured output (`SupervisorDecision`) with temperature 0 — routing is never left to chance.
- **Session-scoped memory**: Conversation history and order auth state are maintained per session, so the agent remembers context across turns.
- **Order authentication flow**: Before an order agent can act, the system verifies the technician's identity via employee ID — modelling a real B2B procurement gate.
- **Low-stock alerting**: The recommendation agent fires automatically mid-conversation when a retrieved part is running low, without the user needing to ask.
- **Scoped tool use**: Each agent only has access to the tools relevant to its task — product agents cannot touch order tools, and vice versa.

---

## Frontend

React (CRA) chat interface styled to match PartSelect's branding.

**Features:**
- **Streaming responses** via SSE — tokens appear as the LLM generates them, no waiting for full response
- **Product cards** — parts returned by the agent render as structured cards with part number, price, stock level, and an "Add to Cart" button
- **Cart overlay** — persists across the conversation; adding a part triggers a real backend cart call
- **Suggested prompts** — onboarding chip buttons covering the four main use cases
- **Typing indicator** — animated dots while the agent is thinking
- **Markdown rendering** — agent responses (tables, bold text, lists) render properly

---

## Backend

FastAPI server with a LangGraph multi-agent graph as the core.

**Tools available to agents:**
- `retrieve_parts` — semantic search over the ChromaDB parts catalog
- `lookup_part_by_number` — direct part number lookup
- `get_parts_for_model` — all parts compatible with a given appliance model
- `search_partselect` — live Tavily-powered web search scoped to partselect.com
- `add_to_cart` / `get_cart` — session-scoped cart management
- `get_emp_history` — CRM connector mock (order history, open tickets, account info)
- `get_estimated_delivery` — delivery ETA based on warehouse location and stock level

**Observability:** Every graph run is traced in LangSmith, providing full visibility into which agent ran, which tools were called, and what decisions were made at each step.

---

## Project Structure

```
case-study-instalily/
├── backend/
│   ├── agents/              # (reserved for future agent expansion)
│   ├── data/
│   │   ├── mock_data.py     # mock CRM/inventory/warehouse data
│   │   ├── seed_data.py     # parts catalog (used to populate ChromaDB)
│   │   └── seed_chroma.py   # one-time script to seed the vector database
│   ├── config.py            # env var loading and model config
│   ├── graph.py             # LangGraph graph definition (nodes, edges, routing)
│   ├── main.py              # FastAPI app and SSE streaming endpoint
│   ├── prompts.py           # all system prompts for each agent
│   ├── state.py             # AgentState TypedDict and SupervisorDecision schema
│   └── tools/
│       └── tools.py         # all LangChain tools
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ChatWindow.js   # main chat UI with streaming and suggested prompts
│       │   ├── ProductCard.js  # part display card with add-to-cart
│       │   └── Cart.js         # cart overlay
│       └── api/
│           └── api.js          # SSE client for streaming backend calls
├── .env.example             # required environment variables
├── pyproject.toml           # Python dependencies (uv)
└── README.md
```

---

## Setup

1. Copy `.env.example` to `.env` and fill in your API keys.
2. Install dependencies: `uv sync`
3. Seed the vector database: `python -m backend.data.seed_chroma`
4. Start the backend: `uvicorn backend.main:app --reload`
5. Start the frontend: `cd frontend && npm install && npm start`

---

## Future Work

- **Visual part identification**: Allow users to upload a photo of a broken part — use a vision model to identify the part number automatically. This is especially useful for field technicians who have the part in hand but not the manual.
- **LangGraph deep agent orchestrator**: Replace flat conditional routing with a true supervisor agent that maintains a scratchpad, reasons about which sub-agent to call next, and loops back for multi-step queries — mapping more closely to Instalily's InstaWorkers model.
