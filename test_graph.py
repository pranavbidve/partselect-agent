from backend.graph import graph
from langchain_core.messages import HumanMessage

print("PartSelect Agent — type your question or 'quit' to exit\n")

while True:
    q = input("You: ").strip()
    if q.lower() in ("quit", "exit", "q"):
        break
    if not q:
        continue
    result = graph.invoke({"messages": [HumanMessage(content=q)]})
    print(f"[intent: {result['intent']}]")
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"[tool called: {[tc['name'] for tc in msg.tool_calls]}]")
    print(f"Agent: {result['messages'][-1].content}")
    print()
