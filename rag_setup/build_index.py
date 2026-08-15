"""
build_index.py

Embeds cleaned chunks and stores them in a local, persistent Chroma vector DB.

Prereq: pip install chromadb sentence-transformers

Usage:
    python build_index.py cleaned_chunks.jsonl ./chroma_db
"""

import sys
import json
import chromadb
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"   # small, fast, runs on CPU, no API key needed
COLLECTION_NAME = "dgcr_posts"
BATCH_SIZE = 64


def load_chunks(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def main(chunks_path, db_path):
    records = load_chunks(chunks_path)
    print(f"Loaded {len(records)} chunks")

    model = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        texts = [r["text"] for r in batch]
        ids = [r["id"] for r in batch]
        metadatas = [
            {
                "thread_title": r["thread_title"],
                "thread_url": r["thread_url"],
                "author": r["author"],
                "post_date": r["post_date"],
            }
            for r in batch
        ]
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        print(f"Indexed {min(i + BATCH_SIZE, len(records))}/{len(records)}")

    print(f"Done. Index stored at {db_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python build_index.py <cleaned_chunks.jsonl> <chroma_db_path>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
