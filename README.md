# DGCR LLM

Scrape forum posts, turn them into chunks, store embeddings in Chroma, and
ask a local Ollama model questions about the retrieved text.

## Install the command

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
dgcr_llm --help
```

The editable install (`-e`) registers `dgcr_llm` in your virtual environment
and uses the scripts in this checkout. Keep the checkout in place; this is a
local development wrapper, not a standalone distributable package. Code edits
take effect without reinstalling. Activate this venv when opening a new terminal.

Install the Ollama Windows application separately and pull `llama3.2` before
querying. The Python `ollama` dependency is only its client library.

## Commands

```powershell
dgcr_llm scrape
dgcr_llm clean
dgcr_llm index
dgcr_llm query
```

| Command | Default behavior |
| --- | --- |
| `scrape` | Run `spider1`, writing `scraping/scrapy_scrape/posts.jsonl` |
| `clean` | Read those posts and write `cleaning/cleaned_chunks.jsonl` |
| `index` | Read those chunks and store embeddings in `chroma_db` |
| `query` | Query `chroma_db` using the interactive Ollama loop; enter `quit` to exit |

Defaults always point to this checkout, even when you run the command from
another folder. Paths you explicitly supply are relative to your current folder.
Output parent folders must already exist.

```powershell
dgcr_llm scrape --output ./sample_posts.jsonl
dgcr_llm clean --input ./sample_posts.jsonl --output ./sample_chunks.jsonl
dgcr_llm index --input ./sample_chunks.jsonl --db ./sample_db
dgcr_llm query --db ./sample_db
dgcr_llm clean --help
```

Scraping replaces the selected output file. The current spider selects the
eighth thread on the first forum listing page and follows pages within that
thread. Cleaning also replaces its output file. Indexing retains the existing
script's `collection.add` behavior; it does not update existing chunk IDs.

The wrapper launches each existing script with the same Python environment and
passes through its output and exit status. The original scripts can still be
run directly. Without installing the command, you can also use
`python dgcr_cli.py clean` (and the other subcommands) from the repo root.
