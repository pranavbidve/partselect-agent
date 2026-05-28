from typing import Optional, TypedDict, Annotated, Literal
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


class SupervisorDecision(BaseModel):
    intent: Literal["product", "compatibility", "troubleshoot", "order", "guard"]
    reasoning: str

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    intent: Optional[str]
    retrieved_parts: Optional[list[dict]]
    low_stock_parts: Optional[list[str]]
    is_off_topic: Optional[bool]
    customer_id: Optional[str]
    session_id: Optional[str]
    order_asked_name: Optional[bool]
    order_verified: Optional[bool]