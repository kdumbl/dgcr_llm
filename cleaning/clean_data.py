"""
clean_data.py

Takes raw Scrapy output (JSON Lines, one post per line) and turns it into
clean text chunks ready to be embedded for RAG.

Expected input schema per line (from spider1):
{
    "thread_title": "Winthrop Gold Course Review",
    "thread_url": "https://www.dgcoursereview.com/threads/example.12345/",
    "post_url": "https://www.dgcoursereview.com/threads/example.12345/post-67890",
    "post_id": "67890",
    "author": "discgolfer99",
    "timestamp": "2024-03-01T12:00:00-0500",
    "content": "<div>Raw HTML of the post body...</div>"
}

Produce this input by having your spider yield one item per forum post, then
run: scrapy crawl spider1 -O posts.jsonl

Usage:
    python clean_data.py posts.jsonl cleaned_chunks.jsonl
"""

import sys
import json
import re
from urllib.parse import urlsplit, urlunsplit
from bs4 import BeautifulSoup

MAX_CHUNK_CHARS = 1200   # roughly 300-400 tokens - a safe chunk size for retrieval
OVERLAP_CHARS = 150


def html_to_text(html: str) -> str:
    """Strip HTML, drop quoted replies, collapse whitespace."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")

    # Drop quoted-post blocks so you don't index the same reply twice.
    # Forum templates vary - inspect a real post's HTML and adjust these
    # selectors (view-source on a thread page is the fastest way to check).
    for tag in soup.select("blockquote, .quote, .bbcode_quote"):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def chunk_text(text: str, max_chars=MAX_CHUNK_CHARS, overlap=OVERLAP_CHARS):
    """Simple character-based chunking with overlap for long posts."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def main(in_path, out_path):
    # Group posts by thread so replies stay associated with their thread title.
    threads = {}
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            post = json.loads(line)
            # Scrapy records the current page URL; group all pages of a thread.
            url = urlsplit(post["thread_url"])
            path = re.sub(r"/page-\d+/?$", "/", url.path)
            key = urlunsplit((url.scheme, url.netloc, path, "", ""))
            threads.setdefault(key, []).append(post)

    n_chunks = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for thread_url, posts in threads.items():
            title = posts[0].get("thread_title", "")

            for post in posts:
                body = html_to_text(post.get("content", ""))
                if len(body) < 20:          # skip empty/near-empty posts
                    continue

                for i, chunk in enumerate(chunk_text(body)):
                    record = {
                        "id": f"{thread_url}::{post['post_id']}::{i}",
                        "thread_title": title,
                        "thread_url": thread_url,
                        "post_id": str(post["post_id"]),
                        "post_url": post.get("post_url") or "",
                        "author": post.get("author") or "",
                        # Keep the output field expected by build_index.py.
                        "post_date": post.get("timestamp") or "",
                        # Prepend the thread title so the chunk is self-contained
                        # once it's retrieved out of context at query time.
                        "text": f"Thread: {title}\n{chunk}",
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    n_chunks += 1

    print(f"Wrote {n_chunks} chunks from {len(threads)} threads to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clean_data.py <scrapy_output.jsonl> <cleaned_chunks.jsonl>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
