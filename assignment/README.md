# Task 1 — Knowledge Brain

Python/FastAPI service that crawls the Brilliant Directories Solution Center, stores article chunks and embeddings, answers questions with Claude using retrieved evidence, tracks ingestion changes, and escalates unanswered questions for human review.

## Requirements

- Python 3.11 or 3.12
- Anthropic API key for Claude-generated answers
- Internet access for the public help center and first-time embedding model download

## Run locally

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs.

## First ingestion

```bash
curl -X POST http://127.0.0.1:8000/ingestion/run
```

The initial full crawl can take a while. It uses a small concurrency limit, delay, retries and a persistent manifest. The current implementation hashes article content to skip re-embedding unchanged pages. It processes only URLs in the configured sitemap host.

## Ask a question

```bash
curl -X POST http://127.0.0.1:8000/query \\
  -H "Content-Type: application/json" \\
  -d '{"question":"How do I change my website logo?","top_k":5}'
```

## Useful endpoints

- `GET /health`
- `POST /query`
- `POST /ingestion/run`
- `GET /ingestion/status`
- `GET /escalations`
- `POST /escalations/{id}/resolve`

## Daily refresh

Run `python -m app.scheduler` to start the API with a daily UTC sitemap refresh. For a deployment, use a dedicated scheduler/worker and protect operational endpoints with authentication before exposing them publicly.

## Important limitations

This is a capstone starter, not production-hardened software. Article image URLs and surrounding context are indexed, but image pixels are not yet downloaded or interpreted by a vision model. Retrieval currently uses dense embeddings and a simple similarity threshold; evaluate and tune it against your own labelled cases. Removed URLs are deactivated based on sitemap membership, so verify that the sitemap only contains article URLs. The API has no authentication yet. Run the evaluation suite and record actual quality, latency and cost before claiming performance.
