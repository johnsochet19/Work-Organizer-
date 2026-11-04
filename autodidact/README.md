# Autodidact: an AI that teaches itself

Autodidact is a research agent that builds its own "brain" from free sources on the web, and builds its own toolset by finding new free APIs and learning how to use them.
It runs on plain Python 3.10+ with **no installs and no keys required**.

```bash
cd autodidact
python -m autodidact learn "how vaccines work" --cycles 10   # give it a starting interest
python -m autodidact run --forever --interval 30              # let it keep going on its own
python -m autodidact ask "what is an mRNA vaccine?"           # ask it what it learned (with sources)
python -m autodidact report -o knowledge.md                   # everything it knows, as a document
```

Stop it any time with Ctrl+C. Everything is saved in `autodidact_data/brain.db`, and it picks up where it left off.

## How it "builds itself"

Each research cycle:

1. **Picks a topic** from its research queue. When the queue runs dry, it gets curious about concepts it keeps running into but hasn't studied yet.
2. **Chooses where to look** with a multi-armed bandit: it favours sources that have taught it the most new things, but keeps trying ones it hasn't used much.
3. **Reads and remembers.** It indexes every passage for search and extracts key concepts. It also links concepts that appear together into a knowledge graph.
4. **Decides what to learn next.** New concepts that connect strongly to the current topic and to its mission are queued as follow-up topics.
5. **Improves itself** every few cycles:
   - **Self-tuning.** It retires sources that keep teaching it nothing. It widens or narrows how much it reads per topic based on how much it's learning, and it explores more when ideas run low.
   - **Self-extension.** It reads the community directory of free public APIs and picks ones that match its interests. It probes each with a real query and works out which JSON fields hold the useful text. Each API that works is saved as a new source. If you add an Anthropic API key, it can also read an API's documentation page and work out the query URL itself.

Watch it happen with `python -m autodidact journal`, `sources`, and `topics`.

## Built-in sources (all free, no key)

| Source | What it gives |
|---|---|
| Wikipedia | Full encyclopedia articles |
| arXiv | Research paper abstracts (CS, physics, math, bio) |
| PubMed (NIH) | Biomedical paper abstracts |
| Crossref | Scholarly works with abstracts |
| Hacker News | Tech stories, plus the pages they link to |
| Stack Overflow | Programming Q&A |
| GitHub | Open-source projects |
| Open Library | Books and their subjects |
| DuckDuckGo | Instant-answer summaries |

APIs it discovers on its own appear in `python -m autodidact sources` with kind `learned`.

## Optional: give it a language model

```bash
export ANTHROPIC_API_KEY=sk-ant-...        # optional
export AUTODIDACT_MODEL=claude-sonnet-5-5  # optional, this is the default
```

With a key, `ask` writes answers in prose with numbered citations, and self-extension can read API docs. Without one, answers are built from the best-matching sentences it has read, and they still list their sources.

## Safety and manners

- **It never runs code it downloads.** A self-discovered source is a small JSON recipe: a URL template plus the names of the fields to read. Recipes are checked against a live response before they're kept.
- **It's polite to websites.** It obeys `robots.txt`, waits at least 1 second between hits to the same site (`--politeness`), caps page size, and caches responses for a day.
- It only uses APIs that need no key and use HTTPS.
- It learns what sources *say*. That isn't the same as truth, so it always shows where an answer came from.

## Files

| File | Job |
|---|---|
| `autodidact/agent.py` | The research loop, source bandit, follow-up topics, self-tuning |
| `autodidact/brain.py` | SQLite memory: documents, search index (BM25), concepts, graph, queue, journal |
| `autodidact/discover.py` | Finds, probes and learns new free APIs |
| `autodidact/sources.py` | Built-in sources plus the runner for learned recipes |
| `autodidact/text.py` | HTML to text, key-phrase extraction, summaries |
| `autodidact/net.py` | Polite HTTP: robots.txt, rate limits, cache |
| `autodidact/answer.py` | Cited answers and the knowledge report |
| `autodidact/llm.py` | Optional Claude hookup |

## Tests

```bash
python -m unittest discover -s tests
```

The tests run the whole loop against a simulated web: researching, queuing follow-ups, answering, discovering a new API, rejecting a useless one, retiring a bad source, and obeying robots.txt.
