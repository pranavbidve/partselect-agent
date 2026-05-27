import json
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

sessions: dict[str, list] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    customer_id: Optional[str] = "CUST-001"


@app.get("/health")
def health():
    return {"status": "ok", "project": LANGSMITH_PROJECT}


@app.post("/chat")
async def chat(request: ChatRequest):
    history = sessions.get(request.session_id, [])
    history_len = len(history)
    history = history + [HumanMessage(content=request.message)]

    async def generate():
        final_state = None

        async for stream_type, data in graph.astream(
            {"messages": history, "customer_id": request.customer_id, "session_id": request.session_id},
            stream_mode=["messages", "values"],
        ):
            if stream_type == "messages":
                chunk, meta = data
                # Only stream AIMessage text — skip ToolMessages and tool call chunks
                if not isinstance(chunk, AIMessage):
                    continue
                if getattr(chunk, "tool_calls", None):
                    continue
                content = chunk.content
                if not content:
                    continue
                if isinstance(content, list):
                    text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
                else:
                    text = content
                if text:
                    node = meta.get("langgraph_node", "")
                    yield {"data": json.dumps({"type": "token", "content": text, "node": node})}
            elif stream_type == "values":
                final_state = data

        # Only extract parts from tool calls made THIS turn (not from history)
        retrieved_parts = []
        model_parts = []
        if final_state:
            sessions[request.session_id] = final_state["messages"][-20:]
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

        # If get_parts_for_model ran, use those results only (ignore lookup results)
        retrieved_parts = model_parts if model_parts else retrieved_parts

        yield {
            "data": json.dumps({"type": "done", "parts": retrieved_parts}),
            "event": "done",
        }

    return EventSourceResponse(generate())
