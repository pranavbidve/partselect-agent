import asyncio
import json
import re
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage

from backend.config import LANGSMITH_PROJECT
from backend.graph import graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict[str, dict] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    customer_id: Optional[str] = "CUST-001"


@app.get("/health")
def health():
    return {"status": "ok", "project": LANGSMITH_PROJECT}


@app.post("/chat")
async def chat(request: ChatRequest):
    prev = sessions.get(request.session_id, {})
    history = prev.get("messages", [])
    history_len = len(history)
    history = history + [HumanMessage(content=request.message)]

    async def generate():
        final_state = None
        last_node = None
        had_tool_call = False
        try:
            async for stream_type, data in graph.astream(
                {
                    "messages": history,
                    "customer_id": prev.get("customer_id") or request.customer_id,
                    "session_id": request.session_id,
                    "order_asked_name": prev.get("order_asked_name"),
                    "order_verified": prev.get("order_verified"),
                },
                stream_mode=["messages", "values"],
            ):
                if stream_type == "messages":
                    chunk, meta = data
                    if not isinstance(chunk, AIMessage):
                        if meta.get("langgraph_node") == "tools":
                            had_tool_call = True
                        continue
                    node = meta.get("langgraph_node", "")
                    if node == "supervisor":
                        continue
                    if getattr(chunk, "tool_calls", None):
                        had_tool_call = True
                        continue
                    content = chunk.content
                    if not content:
                        continue
                    if isinstance(content, list):
                        text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
                    else:
                        text = content
                    if text:
                        # Insert paragraph break when switching nodes or after tool calls in same node
                        if last_node is not None and (had_tool_call or last_node != node):
                            yield {"data": json.dumps({"type": "token", "content": "\n\n", "node": node})}
                        had_tool_call = False
                        last_node = node
                        yield {"data": json.dumps({"type": "token", "content": text, "node": node})}
                elif stream_type == "values":
                    final_state = data
        except asyncio.CancelledError:
            return

        retrieved_parts = []
        model_parts = []
        if final_state:
            sessions[request.session_id] = {
                "messages": final_state["messages"][-20:],
                "customer_id": final_state.get("customer_id"),
                "order_asked_name": final_state.get("order_asked_name"),
                "order_verified": final_state.get("order_verified"),
            }
            new_messages = final_state["messages"][history_len:]
            for msg in new_messages:
                if not isinstance(msg, ToolMessage):
                    continue
                try:
                    parsed = json.loads(msg.content)
                except (json.JSONDecodeError, TypeError):
                    continue
                parts_list = parsed if isinstance(parsed, list) else [parsed] if isinstance(parsed, dict) else []
                if msg.name == "get_parts_for_model":
                    model_parts.extend(p for p in parts_list if p.get("metadata", {}).get("low_stock"))
                elif msg.name in ("retrieve_parts", "lookup_part_by_number"):
                    retrieved_parts.extend(parts_list)

        retrieved_parts = model_parts if model_parts else retrieved_parts

        seen = set()
        retrieved_parts = [p for p in retrieved_parts if not (pn := p.get("metadata", {}).get("part_number")) or (pn not in seen and not seen.add(pn))]

        if not model_parts and retrieved_parts:
            mentioned = set()
            for msg in new_messages:
                if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
                    content = msg.content
                    text = "".join(b.get("text", "") for b in content if b.get("type") == "text") if isinstance(content, list) else (content or "")
                    mentioned.update(re.findall(r'PS\d+', text))
            if mentioned:
                filtered = [p for p in retrieved_parts if p.get("metadata", {}).get("part_number") in mentioned]
                if filtered:
                    retrieved_parts = filtered

        yield {
            "data": json.dumps({"type": "done", "parts": retrieved_parts}),
            "event": "done",
        }

    return EventSourceResponse(generate())
