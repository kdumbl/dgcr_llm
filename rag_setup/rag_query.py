"""
rag_query.py

Interactive RAG query loop: embeds a question, retrieves the most relevant
forum chunks from Chroma, and asks a local Ollama model to answer using
only that retrieved context.

Prereqs:
    - Ollama installed and running (`ollama serve`)
    - A model pulled, e.g.: `ollama pull llama3.2`
    - build_index.py already run to create the chroma_db directory
    - pip install chromadb sentence-transformers ollama

Usage:
    python rag_query.py ./chroma_db
"""

import sys
import chromadb
import ollama
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "llama3.2"
COLLECTION_NAME = "dgcr_posts"
TOP_K = 5

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about disc golf courses "
    "using excerpts from a disc golf forum. Only use the information in the "
    "provided context. If the context doesn't contain the answer, say so "
    "plainly instead of guessing. Mention which thread a fact came from."
)


def build_prompt(question, results):
    context_blocks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context_blocks.append(
            f"[{meta['thread_title']} - posted by {meta['author']}]\n{doc}"
        )
    context = "\n\n---\n\n".join(context_blocks)
    return f"Context from forum posts:\n\n{context}\n\nQuestion: {question}"


def main(db_path):
    embed_model = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(COLLECTION_NAME)

    print("RAG query loop. Type a question, or 'quit' to exit.\n")
    while True:
        question = input("> ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue

        query_embedding = embed_model.encode([question]).tolist()
        results = collection.query(query_embeddings=query_embedding, n_results=TOP_K)

        if not results["documents"][0]:
            print("No relevant posts found in the index.\n")
            continue

        user_prompt = build_prompt(question, results)
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        print("\n" + response["message"]["content"])

        print("\nSources:")
        seen = set()
        for meta in results["metadatas"][0]:
            if meta["thread_url"] not in seen:
                print(f"  - {meta['thread_title']} ({meta['thread_url']})")
                seen.add(meta["thread_url"])
        print()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "./chroma_db"
    main(db_path)
