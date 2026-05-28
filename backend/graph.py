from backend.config import AGENT_MODEL, REASON_MODEL
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from backend.config import SUPERVISOR_MODEL, LOW_STOCK_THRESHOLD


def agent_messages(messages: list) -> list:
    """Strip tool-call intermediates from prior turns only.
    Preserves the current turn's tool calls so the agent's own loop works correctly."""
    last_human = next((i for i in range(len(messages) - 1, -1, -1) if isinstance(messages[i], HumanMessage)), None)
    if last_human is None:
        return messages
    prior = [
        m for m in messages[:last_human]
        if isinstance(m, (HumanMessage, AIMessage)) and not getattr(m, "tool_calls", None)
    ]
    return prior + messages[last_human:]
from backend.state import AgentState, SupervisorDecision
from backend.tools.tools import PRODUCT_TOOLS, COMPAT_TOOLS, TROUBLE_TOOLS, ORDER_TOOLS, RECOMMENDATION_TOOLS, ALL_TOOLS
    
# i kept temperature 0 coz need a deterministic decision to route
supervisor_llm = ChatOpenAI(model=SUPERVISOR_MODEL, temperature=0)
supervisor_llm_structured = supervisor_llm.with_structured_output(SupervisorDecision)

tool_llm = ChatOpenAI(model = AGENT_MODEL)
reason_llm = ChatAnthropic(model = REASON_MODEL, temperature=0)

product_agent_llm = tool_llm.bind_tools(PRODUCT_TOOLS)
compat_agent_llm = tool_llm.bind_tools(COMPAT_TOOLS)
order_agent_llm = tool_llm.bind_tools(ORDER_TOOLS)
recommend_agent_llm = tool_llm.bind_tools(RECOMMENDATION_TOOLS)
trouble_agent_llm = reason_llm.bind_tools(TROUBLE_TOOLS)


def supervisor_node(state: AgentState) -> dict:
    system = """You are a routing assistant for PartSelect.com, a retailer of refrigerator and dishwasher parts.
Classify the user's latest message into one of these intents:
- product: questions about finding, looking up, or browsing parts — including generic questions like "are there more parts?", "what parts are available?", "do you have X for a dishwasher/refrigerator?", or any part search without a specific model number provided. When in doubt between product and compatibility, use product.
- compatibility: ONLY when the user provides BOTH a specific part number AND a specific appliance model number, and is asking whether they fit together
- troubleshoot: diagnosing a symptom or problem with an appliance
- order: cart, order status, returns, shipping, account or order history
- guard: anything unrelated to refrigerator or dishwasher parts, or empty/unclear messages with no actionable content"""
    decision = supervisor_llm_structured.invoke(
        [SystemMessage(content=system)] + agent_messages(state["messages"])
    )
    intent = decision["intent"] if isinstance(decision, dict) else decision.intent
    return {"intent": intent}


def product_agent(state: AgentState) -> dict:
    system = """You are a product specialist for PartSelect.com. Help users find parts, look up part numbers, and get installation instructions.

Tool usage order — follow this strictly:
1. ALWAYS call retrieve_parts first with a descriptive query (e.g. "Whirlpool dishwasher water inlet valve"). This is your primary source for part numbers, prices, and stock levels.
2. If the user provides a specific part number, call lookup_part_by_number for full details.
3. Only call search_partselect if the user explicitly asks for installation guides or repair instructions, or if retrieve_parts returns no results.

When presenting results, always include part number, name, price, and stock status from the catalog data. Never say you lack pricing or stock info if retrieve_parts returned it."""
    response = product_agent_llm.invoke([SystemMessage(content=system)] + agent_messages(state["messages"]))
    response.name = "product_agent"
    return {"messages": [response]}


def compat_agent(state: AgentState) -> dict:
    system = """You are a compatibility checker. Use your tools to look up the part, then respond as follows:

If COMPATIBLE, output EXACTLY:
Yes — [part_number] is compatible with [model_number].

**Part name:** [part_name]

**Appliance type:** [appliance_type]

If NOT COMPATIBLE THEN OUTPUT THIS:
No — [part_number] is not compatible with [model_number]. if you dont know the part_number or model_number then don't mention this line.

**Part name:** [part_name]

**Appliance type:** [appliance_type]

Then call get_parts_for_model with the model number. List every returned part as:
- [part_number]: [name]

Prefix that list with: "Here are parts that are compatible with [model_number]:"

Rules:
- Base every field strictly on tool results. Do not add information not present in the tool results.
- No extra sentences beyond the formats above."""
    response = compat_agent_llm.invoke([SystemMessage(content=system)] + agent_messages(state["messages"]))
    response.name = "compat_agent"
    return {"messages": [response]}


def trouble_agent(state: AgentState) -> dict:
    system = """You are an expert appliance repair diagnostician for PartSelect.com, specializing in refrigerators and dishwashers.

When a user describes a symptom or problem:
1. Call retrieve_parts with a targeted symptom query (e.g. "ice maker assembly Whirlpool not making ice") to find relevant catalog parts.
2. Optionally call search_partselect to find a PartSelect troubleshooting guide for the symptom.
3. If you want full details (price, stock) on a specific part, call lookup_part_by_number.
4. After gathering tool results, output your diagnosis in EXACTLY this format:

**Diagnosis:** [one-line description of the problem]

**Likely Cause(s):**
- [cause 1]
- [cause 2 if applicable]

**Recommended Parts:**
| Part Number | Name | Price | What It Fixes |
|-------------|------|-------|---------------|
| [part_number] | [name] | $[price] | [brief fix description] |

**Repair Difficulty:** [Easy / Moderate / Advanced]

**Next Steps:** [1–2 sentences: what to check or replace first]

Rules:
- Only include parts returned by your tools. Never invent part numbers.
- Limit Recommended Parts to the top 1–3 most likely fixes.
- If no parts are found in the catalog, say so and recommend a certified technician.
- Output only the formatted sections above — no preamble or extra commentary."""
    response = trouble_agent_llm.invoke([SystemMessage(content=system)] + agent_messages(state["messages"]))
    response.name = "trouble_agent"
    return {"messages": [response]}


def order_agent(state: AgentState) -> dict:
    from backend.data.mock_data import MOCK_CUSTOMERS
    customer_id = state.get("customer_id") or "CUST-001"
    # resolve by name if user mentions one in the latest message
    last_human = next(
        (m.content for m in reversed(state["messages"]) if m.__class__.__name__ == "HumanMessage"), ""
    )
    for cid, cdata in MOCK_CUSTOMERS.items():
        first_name = cdata["name"].split()[0].lower()
        if first_name in last_human.lower():
            customer_id = cid
            break
    system = f"""You are an order management specialist for PartSelect.com. Help users with their cart, order status, returns, and order history.
The current customer's ID is {customer_id}. When the user asks about their order history or account, call get_customer_history with customer_id="{customer_id}" immediately — do not ask the user for their ID.

When presenting order history, use this exact format:

**Order History for [name]**

| Order ID | Part Number | Part Name | Date | Status |
|----------|-------------|-----------|------|--------|
| [order_id] | [part] | [part_name] | [date] | [status] |

If there are open tickets, follow with:

**Open Tickets**
- [ticket description]

No extra commentary beyond the tables above."""
    response = order_agent_llm.invoke([SystemMessage(content=system)] + agent_messages(state["messages"]))
    response.name = "order_agent"
    return {"messages": [response]}


def recommendation_agent(state: AgentState) -> dict:
    low_stock = state.get("low_stock_parts") or []
    system = f"""You are a low stock alert agent. The following parts are low in stock: {low_stock}.

1. Identify the appliance model number the user mentioned in the conversation.
2. Call get_parts_for_model with that model number to retrieve all compatible parts.
3. From those results, find only the parts where low_stock is true.
4. Output EXACTLY the following format and nothing else:



⚠️ Low Stock Alert for Model [model_number]

The part you asked about is compatible and it's running low! Here's what's at risk of selling out:

| Part Number | Name | Price | Stock Level |
|-------------|------|-------|-------------|
| [part_number] | [name] | $[price] | Only [stock_level] left |

We recommend ordering soon to avoid delays!

Rules:
- If the part is not in low stock thenjust skil the low stock alert and return nothing.
- Output only the text above. No preamble, no extra commentary, no restatement of compatibility.
- Add one table row per low-stock part.
- Do not include any part not returned by get_parts_for_model.
"""
    response = recommend_agent_llm.invoke([SystemMessage(content=system)] + agent_messages(state["messages"]))
    response.name = "recommendation_agent"
    return {"messages": [response]}


def guard_node(state: AgentState) -> dict:
    response = AIMessage(
        content="I can only help with refrigerator and dishwasher parts. "
                "Feel free to ask about finding parts, compatibility, troubleshooting, or your orders.",
        name="guard_node",
    )
    return {"messages": [response], "is_off_topic": True}


def route_by_intent(state: AgentState) -> str:
    return state.get("intent", "guard")


def check_stock(state: AgentState) -> str:
    import json as _json
    from langchain_core.messages import ToolMessage as _ToolMessage
    parts = []
    for msg in state.get("messages", []):
        if isinstance(msg, _ToolMessage) and msg.name in ("retrieve_parts", "lookup_part_by_number"):
            try:
                parsed = _json.loads(msg.content)
                if isinstance(parsed, list):
                    parts.extend(parsed)
                elif isinstance(parsed, dict):
                    parts.append(parsed)
            except (ValueError, TypeError):
                pass
    low_stock = [
        p["metadata"]["part_number"]
        for p in parts
        if isinstance(p, dict) and p.get("metadata", {}).get("stock_level", 99) < LOW_STOCK_THRESHOLD
    ]
    return "low_stock" if low_stock else "no_restock"


def route_product_or_compat(state: AgentState) -> str:
    if tools_condition(state) == "tools":
        return "tools"
    return check_stock(state)


def route_after_tools(state: AgentState) -> str:
    known_agents = {"product_agent", "compat_agent", "trouble_agent", "order_agent", "recommendation_agent"}
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and msg.name in known_agents:
            return msg.name
    return "end"

tool_node = ToolNode(ALL_TOOLS)

builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("product_agent", product_agent)
builder.add_node("compat_agent", compat_agent)
builder.add_node("trouble_agent", trouble_agent)
builder.add_node("order_agent", order_agent)
builder.add_node("recommendation_agent", recommendation_agent)
builder.add_node("guard_node", guard_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route_by_intent, {
    "product": "product_agent",
    "compatibility": "compat_agent",
    "troubleshoot": "trouble_agent",
    "order": "order_agent",
    "guard": "guard_node",
})

builder.add_conditional_edges("product_agent", route_product_or_compat, {
    "tools": "tools", "low_stock": "recommendation_agent", "no_restock": END
})
builder.add_conditional_edges("compat_agent", route_product_or_compat, {
    "tools": "tools", "low_stock": "recommendation_agent", "no_restock": END
})
for agent in ["trouble_agent", "order_agent", "recommendation_agent"]:
    builder.add_conditional_edges(agent, tools_condition)

builder.add_conditional_edges("tools", route_after_tools, {
    "product_agent": "product_agent",
    "compat_agent": "compat_agent",
    "trouble_agent": "trouble_agent",
    "order_agent": "order_agent",
    "recommendation_agent": "recommendation_agent",
    "end": END,
})

builder.add_edge("guard_node", END)
builder.add_edge("recommendation_agent", END)


graph = builder.compile()