"""Run once: python -m backend.data.seed_chroma"""
import json
import chromadb
from chromadb.utils import embedding_functions
from backend.data.seed_data import PARTS_CATALOG


def seed():
    client = chromadb.PersistentClient(path="./chroma_db")
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    try:
        client.delete_collection("parts_catalog")
    except Exception:
        pass
    collection = client.create_collection(
        name="parts_catalog",
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    ids, documents, metadatas = [], [], []
    for part in PARTS_CATALOG:
        doc_text = (
            f"{part['name']}. {part['description']} "
            f"Fixes: {', '.join(part['symptoms'])}. "
            f"Compatible with: {', '.join(part['compatible_models'])}. "
            f"Category: {part['category']}. Brand: {part['brand']}."
        )
        meta = {k: v for k, v in part.items() if k not in ("description", "symptoms", "compatible_models")}
        meta["symptoms"] = json.dumps(part["symptoms"])
        meta["compatible_models"] = json.dumps(part["compatible_models"])

        ids.append(part["part_number"])
        documents.append(doc_text)
        metadatas.append(meta)

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Seeded {len(ids)} parts into ChromaDB.")


if __name__ == "__main__":
    seed()
