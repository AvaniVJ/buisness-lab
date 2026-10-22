# Task 3 — Meeting to Scope of Work

Python/FastAPI multi-stage agent workflow that turns meeting transcripts into structured requirements, product-feasibility checks through Task 1's Knowledge Brain API, hour estimates, scope of work, proposal drafts, and follow-up change reports.

## Requirements

- Python 3.11+
- Task 1 Knowledge Brain running at `http://127.0.0.1:8000`
- Anthropic API key

## Run

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Set ANTHROPIC_API_KEY and check hourly rate/currency
uvicorn app.main:app --reload --port 8001
```

Open `http://127.0.0.1:8001/docs`.

## Analyse a transcript

```bash
curl -X POST http://127.0.0.1:8001/projects/analyse \
 -H "Content-Type: application/json" \
 -d '{"project_id":"website-refresh-01","meeting_label":"initial","transcript":"Client: We need to improve website search. We want category filters and a better mobile layout. Consultant: Which categories and mobile devices should be supported? Client: Category and location filters are required. We need to confirm the target date and budget."}'
```

The endpoint returns requirements, knowledge-backed feasibility labels, estimated hours and price ranges, a scope draft, a proposal draft, and a pending human-approval status.

## Approve a baseline

Use the `baseline_id` returned by analysis:

```bash
curl -X POST http://127.0.0.1:8001/baselines/1/review \
 -H "Content-Type: application/json" \
 -d '{"reviewer":"senior-consultant","approved":true,"notes":"Reviewed requirements and assumptions."}'
```

## Follow-up comparison

Submit the follow-up transcript with `meeting_label:"follow-up"` and `approved_baseline_id` set to the approved baseline ID. The result includes a change report comparing against the approved baseline.

## API

- `GET /health`
- `POST /projects/analyse`
- `GET /projects/{project_id}/baselines`
- `GET /baselines/{baseline_id}`
- `POST /baselines/{baseline_id}/review`

## Design

Agent responsibilities are separated into transcript analysis, product feasibility, estimation, scope generation, proposal generation, and change comparison. Long transcripts are processed in overlapping sections before requirements are merged. Each requirement keeps an evidence quote and uncertainty status.

## Limitations

- This is a starter implementation; validate its outputs and run tests before relying on estimates.
- Estimates and price ranges are model-generated planning aids, not contractual quotes.
- The Knowledge Brain API must be available for feature checks; missing evidence is classified as needing clarification.
- The current text chunking uses character windows, not a production-grade speaker/timestamp-aware transcript parser.
- Authentication, file uploads, a visual approval UI, richer audit controls, and production observability are not included.
- The capstone requires at least three role-played transcripts, including a follow-up; create and test these using consented recordings or transcripts.
- Run at least 20 evaluation cases, compare model configurations, and report measured quality, latency, cost, and failures. Do not invent scores.
