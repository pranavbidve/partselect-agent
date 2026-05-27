from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from backend.config import GROQ_MODEL, SUPERVISOR_MODEL, LOW_STOCK_THRESHOLD
from backend.state import AgentState, SupervisorDecision
from backend.tools.tools import PRODUCT_TOOLS, COMPAT_TOOLS, TROUBLE_TOOLS, ORDER_TOOLS, RECOMMENDATION_TOOLS, ALL_TOOLS
    
# i kept temperature 0 coz need a deterministic decision to route
supervisor_llm = ChatGroq(model=SUPERVISOR_MODEL, temperature=0)
supervisor_llm_structured = supervisor_llm.with_structured_output(SupervisorDecision)

agent_llm = ChatGroq(model=GROQ_MODEL, temperature=0) 
# special_llm = ChatOpenAI(model = 'gpt-5.4-mini')

product_agent_llm = agent_llm.bind_tools(PRODUCT_TOOLS)
compat_agent_llm = agent_llm.bind_tools(COMPAT_TOOLS)
trouble_agent_llm = agent_llm.bind_tools(TROUBLE_TOOLS)
order_agent_llm = agent_llm.bind_tools(ORDER_TOOLS)
recommend_agent_llm = agent_llm.bind_tools(RECOMMENDATION_TOOLS)



def supervisor_node(state: AgentState) -> dict:
    system = """You are a routing assistant for PartSelect.com, a retailer of refrigerator and dishwasher parts.
Classify the user's latest message into one of these intents:
- product: questions about a specific part (specs, installation, part number lookup)
- compatibility: whether a part fits a specific appliance model
- troubleshoot: diagnosing a symptom or problem with an appliance
- order: cart, order status, returns, shipping, account or order history
- guard: anything unrelated to refrigerator or dishwasher parts"""
    decision = supervisor_llm_structured.invoke(
        [SystemMessage(content=system)] + state["messages"]
    )
    intent = decision["intent"] if isinstance(decision, dict) else decision.intent
    return {"intent": intent}


def product_agent(state: AgentState) -> dict:
    system = """You are a product specialist for PartSelect.com. Help users find parts, look up part numbers,
and get installation instructions. Always include the part number, price, and stock status when available."""
    response = product_agent_llm.invoke([SystemMessage(content=system)] + state["messages"])
    response.name = "product_agent"
    return {"messages": [response]}


def compat_agent(state: AgentState) -> dict:
    system = """You are a compatibility specialist for PartSelect.com. Help users determine if a part fits
their specific appliance model. Always confirm both the model number and part number in your response."""
    response = compat_agent_llm.invoke([SystemMessage(content=system)] + state["messages"])
    response.name = "compat_agent"
    return {"messages": [response]}


def trouble_agent(state: AgentState) -> dict:
    system = """You are an appliance repair specialist for PartSelect.com. Diagnose problems with
refrigerators and dishwashers and recommend the parts needed to fix them. Always suggest specific part numbers."""
    response = trouble_agent_llm.invoke([SystemMessage(content=system)] + state["messages"])
    response.name = "trouble_agent"
    return {"messages": [response]}


def order_agent(state: AgentState) -> dict:
    system = """You are an order management specialist for PartSelect.com. Help users with their cart,
order status, returns, and order history. Use get_customer_history when the user asks about their account."""
    response = order_agent_llm.invoke([SystemMessage(content=system)] + state["messages"])
    response.name = "order_agent"
    return {"messages": [response]}


def recommendation_agent(state: AgentState) -> dict:
    low_stock = state.get("low_stock_parts") or []
    system = f"""You are a proactive product advisor for PartSelect.com.
The following parts are low in stock: {low_stock}.
For each, find in-stock alternatives using your tools and present them clearly with part numbers and availability."""
    response = recommend_agent_llm.invoke([SystemMessage(content=system)] + state["messages"])
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
    parts = state.get("retrieved_parts") or []
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