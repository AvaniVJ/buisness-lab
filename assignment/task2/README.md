# Task 2 — Inbox Agent

Strict TypeScript/Node.js service that calls Task 1's Knowledge Brain API, drafts email replies with Claude, stores drafts and human reviews, and tracks unchanged approvals per category.

## Run
Requires Node.js 20+, Task 1 running at `http://127.0.0.1:8000`, and an Anthropic API key.

```bash
npm install
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env
npm run dev
```
Runs at `http://127.0.0.1:3002`.

## Draft
```bash
curl -X POST http://127.0.0.1:3002/emails/draft -H "Content-Type: application/json" -d '{"from":"client@example.com","subject":"Logo help","body":"How do I change my website logo?"}'
```
## Review
Replace `1` with the returned email ID:
```bash
curl -X POST http://127.0.0.1:3002/emails/1/review -H "Content-Type: application/json" -d '{"action":"approve","reviewer":"support-agent"}'
```
For edits use `"action":"edit"`, `"finalReply":"..."`, and `"reviewer":"..."`. Other actions: `reject`, `escalate`.

## API
- `GET /health`
- `POST /emails/draft`
- `GET /emails`, `GET /emails/:id`
- `POST /emails/:id/review`
- `GET /learning/status`

## Learning and safety
The system stores generated/final replies and review outcomes. Twenty consecutive approvals with unchanged text mark a category as eligible for a future autonomy trial; this starter never sends email automatically. Streaks reset after edits, rejection, or escalation. Do not auto-send high-risk categories.

The included seed script provides 10 examples only. The capstone requires at least 50 realistic, labelled emails and at least 20 evaluation cases. Add those and report actual quality, latency, cost, and failure rates in EVALS.md.

## Limitations
No email-provider integration or UI is included; review is API-based. Feedback is recorded, but prompt updates are not automatic. Add authentication, rate limiting, PII controls, and operational monitoring before production use. Do not claim unmeasured evaluation results.
