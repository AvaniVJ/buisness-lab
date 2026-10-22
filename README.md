# AI Tech Consultant — Integrated Capstone

An AI-powered consulting workflow built from three integrated tasks:

1. **Knowledge Brain** — answers product questions using indexed support documentation and citations.
2. **Inbox Agent** — drafts customer email responses for human review and learns from reviewer feedback.
3. **Meeting-to-Scope Agent** — converts meeting transcripts into requirements, estimates, scopes of work, and proposals.

The Knowledge Brain acts as the shared source of product knowledge for the other two agents.

## Project Architecture

```text
Brilliant Directories Support Center
                 |
                 v
       Task 1: Knowledge Brain
       Python + FastAPI + Claude
                 |
          Knowledge API
             /       \
            v         v
      Task 2          Task 3
   Inbox Agent     Meeting-to-Scope
 TypeScript/Node      Python
   Email drafts    Requirements
   Human review    Estimates
   Feedback        Proposals
                   Change detection
```

## Technologies Used

- Python
- TypeScript and Node.js
- FastAPI and Express
- Claude API
- SQLite
- Sentence Transformers and retrieval-augmented generation (RAG)
- REST APIs
- Automated tests

## Requirements

Install the following before running the project:

- Python 3.11 or newer
- Node.js 20 or newer and npm
- An Anthropic API key
- Internet access for initial documentation ingestion and model downloads

Check that the Claude model configured in each `.env` file is currently available to your Anthropic account.

## Installation and Setup

Clone or download the project repository, then open three terminal windows.

### Task 1: Knowledge Brain

```bash
cd task1_knowledge_brain

python -m venv .venv
```

Activate the virtual environment.

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies and configure the environment:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure your Anthropic API key.

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Run the initial documentation ingestion:

```bash
curl -X POST http://127.0.0.1:8000/ingestion/run
```

API documentation:

http://127.0.0.1:8000/docs

### Task 2: Inbox Agent

Open a second terminal:

```bash
cd task2_inbox_agent
npm install
```

Copy `.env.example` to `.env`, configure your Anthropic API key, and set:

```env
KNOWLEDGE_BRAIN_URL=http://127.0.0.1:8000
```

Start the development server:

```bash
npm run dev
```

The API runs at:

http://127.0.0.1:3002

The current seed script creates only 10 example emails. Expand the dataset to at least 50 realistic customer emails before final submission.

### Task 3: Meeting-to-Scope Agent

Open a third terminal:

```bash
cd task3_meeting_to_scope

python -m venv .venv
```

Activate the virtual environment using the instructions from Task 1.

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`, configure your Anthropic API key, and verify the Knowledge Brain API URL.

Start the server:

```bash
uvicorn app.main:app --reload --port 8001
```

API documentation:

http://127.0.0.1:8001/docs

## Task 1: Knowledge Brain

The Knowledge Brain collects and indexes documentation from the Brilliant Directories Solution Center sitemap.

Its responsibilities include:

- Crawling sitemap URLs.
- Extracting article text and image references.
- Retrieving relevant information for user questions.
- Generating answers with supporting citations.
- Escalating questions when the available evidence is insufficient.
- Recording expert resolutions for future use.
- Supporting documentation refreshes.

Main endpoints:

- `GET /health`
- `POST /query`
- `POST /ingestion/run`
- `GET /ingestion/status`
- `GET /escalations`
- `POST /escalations/{id}/resolve`

**Current limitation:** Image URLs and associated text can be indexed, but visual answers contained only in screenshots are not yet fully supported by image-vision processing.

## Task 2: Inbox Agent

The Inbox Agent creates customer email drafts and sends them through a human-review workflow.

Its responsibilities include:

- Accepting incoming customer emails.
- Querying the Knowledge Brain for relevant product information.
- Generating email response drafts.
- Supporting approval, editing, rejection, and escalation.
- Recording reviewer feedback.
- Tracking consecutive unchanged approvals by category.

Main endpoints:

- `GET /health`
- `POST /emails/draft`
- `GET /emails`
- `GET /emails/:id`
- `POST /emails/:id/review`
- `GET /learning/status`

After 20 consecutive unchanged approvals in a category, that category can be marked eligible for a future autonomy trial. Automatic email sending is not implemented in the current starter code.

## Task 3: Meeting-to-Scope Agent

The Meeting-to-Scope Agent transforms meeting transcripts into structured project deliverables.

Its responsibilities include:

- Processing long meeting transcripts.
- Extracting requirements and requested functionality.
- Checking existing product features through the Knowledge Brain API.
- Distinguishing existing functionality from potential custom development.
- Producing estimates and a draft scope of work.
- Generating a proposal draft.
- Comparing follow-up discussions against an approved baseline.
- Highlighting potential scope changes for human review.

Main endpoints:

- `GET /health`
- `POST /projects/analyse`
- `GET /projects/{project_id}/baselines`
- `GET /baselines/{baseline_id}`
- `POST /baselines/{baseline_id}/review`

Estimates are planning aids and must be reviewed before being treated as contractual commitments.

## Testing

Run Task 1 tests:

```bash
cd task1_knowledge_brain
pytest
```

Run Task 2 tests and build:

```bash
cd task2_inbox_agent
npm test
npm run build
```

Run Task 3 tests:

```bash
cd task3_meeting_to_scope
pytest
```

## Evaluation and Deliverables

Before final submission:

- Create at least 20 evaluation cases for each task.
- Compare at least two models where required and report measured results.
- Record answer quality, citation accuracy, latency, cost, and failure cases.
- Create at least 50 realistic customer email examples.
- Role-play at least three client meetings, including a follow-up meeting.
- Retain the full AI chat conversations required by the assignment.
- Write `DESIGN.md` (3–5 pages).
- Write `EVALS.md` (2–3 pages).
- Write `AI_LOG.md` (maximum one page), including useful prompts and a genuinely rejected AI answer.
- Record a demo video of no more than 10 minutes, with your face visible during the first 30 seconds.
- Demonstrate all three tasks working together and include at least one failure case.

Do not invent evaluation results. Report actual measurements from your experiments.

## Known Limitations

This repository is a starter implementation and is not production-ready.

- Screenshot image understanding needs further implementation and testing.
- Retrieval thresholds need evaluation and tuning.
- Authentication and rate limiting are not fully implemented.
- The Inbox Agent does not include a production email-provider integration or review interface.
- Reviewer feedback is recorded, but automatic prompt improvement is not fully implemented.
- Transcript processing and change detection require further evaluation.
- Model-generated estimates require human validation.
- Evaluation datasets, measured results, and demo evidence must be completed before submission.

## Security Notice

Keep API keys in environment variables. Never commit `.env` files or expose API keys in source control. Review customer information carefully and add appropriate authentication, privacy safeguards, logging, and access controls before any production deployment.

## Conclusion

This project demonstrates an integrated AI consulting workflow in which a shared Knowledge Brain supports customer email drafting and meeting-based project scoping. Human review remains central to handling uncertain answers, approving customer communications, and validating proposed project commitments.
