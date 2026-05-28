import json
from datetime import date, timedelta
from langchain_core.tools import tool
from tavily import TavilyClient
import chromadb
from chromadb.utils import embedding_functions

from backend.config import TAVILY_API_KEY, LOW_STOCK_THRESHOLD
from backend.data.mock_data import MOCK_CUSTOMERS, MOCK_INVENTORY, WAREHOUSE_SHIPPING_DAYS

tavily = TavilyClient(api_key=TAVILY_API_KEY)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = chroma_client.get_or_create_collection(
    name="parts_catalog",
    embedding_function=embed_fn,
    metadata={"hnsw:space": "cosine"},
)

carts: dict = {}


@tool
def search_partselect(query: str) -> str:
    """Search PartSelect.com for parts, installation guides, compatibility info, or policies."""
    results = tavily.search(query=query, include_domains=["partselect.com"], max_results=5)
    if not results.get("results"):
        return "No results found on PartSelect.com."
    return "\n\n".join(f"[{r['title']}]({r['url']})\n{r['content']}" for r in results["results"])


@tool
def retrieve_parts(query: str) -> str:
    """Semantic search over the parts catalog. Returns up to 5 relevant parts."""
    results = collection.query(query_texts=[query], n_results=5, include=["documents", "metadatas"])
    if not results["documents"][0]:
        return "No matching parts found."
    parts = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        inv = MOCK_INVENTORY.get(meta.get("part_number", ""), {})
        meta["stock_level"] = inv.get("stock_level", meta.get("stock_level", 0))
        meta["low_stock"] = meta["stock_level"] < LOW_STOCK_THRESHOLD
        parts.append({"metadata": meta, "description": doc})
    return json.dumps(parts, indent=2)


@tool
def lookup_part_by_number(part_number: str) -> str:
    """Look up a specific part by part number (e.g. PS11752778)."""
    results = collection.get(where={"part_number": part_number}, include=["documents", "metadatas"])
    if not results["documents"]:
        return f"Part {part_number} not found."
    meta = results["metadatas"][0]
    inv = MOCK_INVENTORY.get(part_number, {})
    meta["stock_level"] = inv.get("stock_level", meta.get("stock_level", 0))
    meta["low_stock"] = meta["stock_level"] < LOW_STOCK_THRESHOLD
    if inv.get("restock_eta"):
        meta["restock_eta"] = inv["restock_eta"]
    return json.dumps({"metadata": meta, "description": results["documents"][0]}, indent=2)


@tool
def get_parts_for_model(model_number: str) -> str:
    """Get all parts compatible with a specific appliance model number (e.g. WDT780SAEM1)."""
    all_results = collection.get(include=["documents", "metadatas"])
    parts = []
    for doc, meta in zip(all_results["documents"], all_results["metadatas"]):
        compatible = json.loads(meta.get("compatible_models", "[]"))
        if model_number in compatible:
            inv = MOCK_INVENTORY.get(meta.get("part_number", ""), {})
            meta["stock_level"] = inv.get("stock_level", meta.get("stock_level", 0))
            meta["low_stock"] = meta["stock_level"] < LOW_STOCK_THRESHOLD
            parts.append({"metadata": meta, "description": doc})
    if not parts:
        return f"No parts found for model {model_number}."
    return json.dumps(parts, indent=2)


@tool
def add_to_cart(part_number: str, session_id: str = "default") -> str:
    """Add a part to the cart by part number."""
    results = collection.get(where={"part_number": part_number}, include=["metadatas"])
    if not results["metadatas"]:
        return f"Part {part_number} not found."
    meta = results["metadatas"][0]
    cart = carts.setdefault(session_id, {})
    if part_number in cart:
        cart[part_number]["quantity"] += 1
    else:
        cart[part_number] = {"part_number": part_number, "name": meta["name"], "price": meta["price"], "quantity": 1}
    item = cart[part_number]
    return f"Added {item['name']} (${item['price']:.2f}) to cart. Qty: {item['quantity']}."


@tool
def get_cart(session_id: str = "default") -> str:
    """Return current cart contents with subtotal."""
    cart = carts.get(session_id, {})
    if not cart:
        return "Your cart is empty."
    items = list(cart.values())
    subtotal = sum(i["price"] * i["quantity"] for i in items)
    return json.dumps({"items": items, "subtotal": round(subtotal, 2)}, indent=2)


@tool
def get_estimated_delivery(part_number: str) -> str:
    """Get estimated delivery date for a part based on stock level and warehouse location."""
    inv = MOCK_INVENTORY.get(part_number)
    if not inv:
        return f"No inventory info found for {part_number}."

    stock = inv.get("stock_level", 0)
    warehouse = inv.get("warehouse", "Chicago-IL")
    shipping_days = WAREHOUSE_SHIPPING_DAYS.get(warehouse, 5)

    if stock >= LOW_STOCK_THRESHOLD:
        delivery = date.today() + timedelta(days=shipping_days)
        return (
            f"In stock at {warehouse}. Estimated delivery: "
            f"{delivery.strftime('%b %d, %Y')} ({shipping_days} business days)."
        )
    elif inv.get("restock_eta"):
        restock = date.fromisoformat(inv["restock_eta"])
        delivery = restock + timedelta(days=shipping_days)
        return (
            f"Low stock at {warehouse}. Restocks {restock.strftime('%b %d')} — "
            f"estimated delivery: {delivery.strftime('%b %d, %Y')}."
        )
    else:
        return f"Part {part_number} is currently out of stock with no restock ETA."


@tool
def get_customer_history(customer_id: str) -> str:
    """Get order history and account info for a customer by CUST-ID. (CRM connector)"""
    customer = MOCK_CUSTOMERS.get(customer_id)
    if not customer:
        return f"Customer {customer_id} not found."
    return json.dumps(customer, indent=2)


PRODUCT_TOOLS        = [search_partselect, retrieve_parts, lookup_part_by_number, get_parts_for_model]
COMPAT_TOOLS         = [lookup_part_by_number, get_parts_for_model]
TROUBLE_TOOLS        = [search_partselect, retrieve_parts, lookup_part_by_number]
ORDER_TOOLS          = [add_to_cart, get_cart, get_customer_history, lookup_part_by_number, get_estimated_delivery]
ALL_TOOLS = [search_partselect, retrieve_parts, lookup_part_by_number, get_parts_for_model, add_to_cart, get_cart, get_customer_history, get_estimated_delivery]
