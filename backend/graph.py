from backend.config import AGENT_MODEL, REASON_MODEL
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from backend.config import SUPERVISOR_MODEL, LOW_STOCK_THRESHOLD
from backend.state import AgentState, SupervisorDecision
from backend.tools.tools import PRODUCT_TOOLS, COMPAT_TOOLS, TROUBLE_TOOLS, ORDER_TOOLS, ALL_TOOLS
from backend.prompts import (
    SUPERVISOR_PROMPT,
    PRODUCT_AGENT_PROMPT,
    COMPAT_AGENT_PROMPT,
    TROUBLE_AGENT_PROMPT,
    ORDER_AGENT_PROMPT,
    RECOMMENDATION_AGENT_PROMPT,
    GUARD_RESPONSE,
    ORDER_AUTH_ASK_NAME,
    ORDER_AUTH_NOT_FOUND,
)

# i kept temperature 0 coz need a deterministic decision to route
supervisor_llm = ChatOpenAI(model=SUPERVISOR_MODEL, temperature=0)
tool_llm = ChatOpenAI(model=AGENT_MODEL)
reason_llm = ChatAnthropic(model=REASON_MODEL, temperature=0)

supervisor_llm_structured = supervisor_llm.with_structured_output(SupervisorDecision)
product_agent_llm = tool_llm.bind_tools(PRODUCT_TOOLS)
compat_agent_llm = tool_llm.bind_tools(COMPAT_TOOLS)
order_agent_llm = tool_llm.bind_tools(ORDER_TOOLS)
recommend_agent_llm = tool_llm
trouble_agent_llm = reason_llm.bind_tools(TROUBLE_TOOLS)


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


def supervisor_node(state: AgentState) -> dict:
    decision = supervisor_llm_structured.invoke(
        [SystemMessage(content=SUPERVISOR_PROMPT)] + agent_messages(state["messages"])
    )
    intent = decision["intent"] if isinstance(decision, dict) else decision.intent
    return {"intent": intent}


def product_agent(state: AgentState) -> dict:
    response = product_agent_llm.invoke([SystemMessage(content=PRODUCT_AGENT_PROMPT)] + agent_messages(state["messages"]))
    response.name = "product_agent"
    return {"messages": [response]}


def compat_agent(state: AgentState) -> dict:
    response = compat_agent_llm.invoke([SystemMessage(content=COMPAT_AGENT_PROMPT)] + agent_messages(state["messages"]))
    response.name = "compat_agent"
    return {"messages": [response]}


def trouble_agent(state: AgentState) -> dict:
    response = trouble_agent_llm.invoke([SystemMessage(content=TROUBLE_AGENT_PROMPT)] + agent_messages(state["messages"]))
    response.name = "trouble_agent"
    return {"messages": [response]}


def order_auth(state: AgentState) -> dict:
    import re
    from backend.data.mock_data import MOCK_TECHNICIANS

    # Direct ID lookup — accept CUST-ID or EMP-ID
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            cust_match = re.search(r'CUST-\d+', msg.content, re.IGNORECASE)
            emp_match = re.search(r'EMP-\d+', msg.content, re.IGNORECASE)
            if cust_match:
                cid = cust_match.group().upper()
                if cid in MOCK_TECHNICIANS:
                    return {"customer_id": cid, "order_verified": True, "order_asked_name": True}
            if emp_match:
                eid = emp_match.group().upper()
                matched = next((k for k, v in MOCK_TECHNICIANS.items() if v.get("emp_id") == eid), None)
                if matched:
                    return {"customer_id": matched, "order_verified": True, "order_asked_name": True}

    # No customer ID provided — ask for name once
    if not state.get("order_asked_name"):
        response = AIMessage(content=ORDER_AUTH_ASK_NAME, name="order_auth")
        return {"messages": [response], "order_asked_name": True}

    # Name was asked — try to match against customer names
    last_human = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), ""
    )
    customer_id = None
    for cid, cdata in MOCK_TECHNICIANS.items():
        if any(part in last_human.lower() for part in cdata["name"].lower().split()):
            customer_id = cid
            break

    if customer_id:
        return {"customer_id": customer_id, "order_verified": True}

    response = AIMessage(content=ORDER_AUTH_NOT_FOUND, name="order_auth")
    return {"messages": [response]}


def order_agent(state: AgentState) -> dict:
    from backend.data.mock_data import MOCK_TECHNICIANS
    customer_id = state.get("customer_id") or "CUST-001"
    # resolve by name if user mentions one in the latest message
    last_human = next(
        (m.content for m in reversed(state["messages"]) if m.__class__.__name__ == "HumanMessage"), ""
    )
    for cid, cdata in MOCK_TECHNICIANS.items():
        first_name = cdata["name"].split()[0].lower()
        if first_name in last_human.lower():
            customer_id = cid
            break
    system = ORDER_AGENT_PROMPT.format(customer_id=customer_id)
    response = order_agent_llm.invoke([SystemMessage(content=system)] + agent_messages(state["messages"]))
    response.name = "order_agent"
    return {"messages": [response]}


def recommendation_agent(state: AgentState) -> dict:
    low_stock = state.get("low_stock_parts") or []
    system = RECOMMENDATION_AGENT_PROMPT.format(low_stock=low_stock)
    response = recommend_agent_llm.invoke([SystemMessage(content=system)] + agent_messages(state["messages"]))
    response.name = "recommendation_agent"
    return {"messages": [response]}


def guard_node(state: AgentState) -> dict:
    response = AIMessage(
        content=GUARD_RESPONSE,
        name="guard_node",
    )
    return {"messages": [response], "is_off_topic": True}


def route_by_intent(state: AgentState) -> str:
    # Mid-auth: name has been asked but not yet verified
    if state.get("order_asked_name") and not state.get("order_verified"):
        return "order_auth"
    intent = state.get("intent", "guard")
    if intent == "order":
        # Already verified this session — skip auth
        return "order_agent" if state.get("order_verified") else "order_auth"
    return intent


def route_after_auth(state: AgentState):
    if state.get("order_verified"):
        return "order_agent"
    return END


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
builder.add_node("order_auth", order_auth)
builder.add_node("order_agent", order_agent)
builder.add_node("recommendation_agent", recommendation_agent)
builder.add_node("guard_node", guard_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route_by_intent, {
    "product": "product_agent",
    "compatibility": "compat_agent",
    "troubleshoot": "trouble_agent",
    "order_auth": "order_auth",
    "order_agent": "order_agent",
    "guard": "guard_node",
})
builder.add_conditional_edges("order_auth", route_after_auth, {
    "order_agent": "order_agent",
    END: END,
})

builder.add_conditional_edges("product_agent", route_product_or_compat, {
    "tools": "tools", "low_stock": "recommendation_agent", "no_restock": END
})
builder.add_conditional_edges("compat_agent", route_product_or_compat, {
    "tools": "tools", "low_stock": "recommendation_agent", "no_restock": END
})
for agent in ["trouble_agent", "order_agent"]:
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
