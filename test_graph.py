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


# ============================================================
# STRESS TESTS — review manually before running
# Run with: uv run python test_graph.py (after uncommenting)
# ============================================================

# import asyncio
# from langchain_core.messages import AIMessage
#
# TESTS = [
#     # (label, message, expected_agent)
#     # --- product_agent ---
#     ("PRODUCT: part install",   "How do I install part PS11752778?",                            "product_agent"),
#     ("PRODUCT: part specs",     "What does part PS11731365 do?",                                "product_agent"),
#     ("PRODUCT: price lookup",   "How much does the ice maker assembly cost?",                   "product_agent"),
#
#     # --- compat_agent ---
#     ("COMPAT: part + model",    "Is PS11752778 compatible with my WDT780SAEM1 model?",         "compat_agent"),
#     ("COMPAT: model fit",       "Will a Whirlpool water inlet valve fit my WRF535SWHZ?",       "compat_agent"),
#
#     # --- trouble_agent ---
#     ("TROUBLE: ice maker",      "The ice maker on my Whirlpool fridge is not working.",        "trouble_agent"),
#     ("TROUBLE: dishwasher",     "My dishwasher is not draining water at the end of the cycle.", "trouble_agent"),
#     ("TROUBLE: fridge warm",    "My fridge is not cooling but the freezer is fine.",            "trouble_agent"),
#
#     # --- order_agent ---
#     ("ORDER: history",          "What have I ordered before?",                                  "order_agent"),
#     ("ORDER: add to cart",      "Add PS11731365 to my cart",                                    "order_agent"),
#     ("ORDER: view cart",        "What's in my cart?",                                           "order_agent"),
#     ("ORDER: return",           "How do I return a part?",                                      "order_agent"),
#
#     # --- guard_node ---
#     ("GUARD: off-topic",        "What is the capital of France?",                               "guard_node"),
#     ("GUARD: weather",          "What's the weather today?",                                    "guard_node"),
#     ("GUARD: unrelated",        "Can you help me write a poem?",                                "guard_node"),
# ]
#
# KNOWN_AGENTS = {"product_agent", "compat_agent", "trouble_agent", "order_agent", "recommendation_agent", "guard_node"}
#
# async def run_test(label, message, expected):
#     final = await graph.ainvoke({"messages": [HumanMessage(content=message)]})
#     agents_called = {msg.name for msg in final["messages"] if isinstance(msg, AIMessage) and msg.name in KNOWN_AGENTS}
#     primary = next(iter(agents_called - {"recommendation_agent"}), "unknown")
#     return {"label": label, "expected": expected, "got": primary, "passed": primary == expected}
#
# async def main():
#     print("\n" + "="*70)
#     print("AGENT ROUTING STRESS TEST")
#     print("="*70)
#     results = []
#     for label, message, expected in TESTS:
#         print(f"\n▶ {label}\n  Query: \"{message}\"")
#         r = await run_test(label, message, expected)
#         print(f"  Expected: {r['expected']} | Got: {r['got']} → {'✅ PASS' if r['passed'] else '❌ FAIL'}")
#         results.append(r)
#     passed = sum(1 for r in results if r["passed"])
#     print(f"\n{'='*70}\nRESULTS: {passed}/{len(results)} passed\n{'='*70}")
#     failures = [r for r in results if not r["passed"]]
#     if failures:
#         print("\nFAILURES:")
#         for f in failures:
#             print(f"  ❌ {f['label']}: expected {f['expected']}, got {f['got']}")
#     else:
#         print("\n🎉 All tests passed!")
#
# if __name__ == "__main__":
#     asyncio.run(main())
