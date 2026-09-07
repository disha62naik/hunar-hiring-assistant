# Hunar Hiring Assistant — Projects 1 & 2

One repo, two flows, sharing the same backend and dashboard pattern:

- **Screenings** (`/screenings`) — Project 1: AI voice screening of inbound candidates
- **Reachout** (`/reachout`) — Project 2: job description → people search → voice reachout → dashboard

```
hunar-assignment/
├── backend/    FastAPI (Python)
└── frontend/   Next.js + TypeScript + shadcn-style UI
```

## 0. Before you do anything: secure the API key

You were given a live Hunar API key in plain text. Do NOT paste it into any file that
gets committed. Both `.env` files are already git-ignored — put real secrets only in:

- `backend/.env` (copy from `backend/.env.example`)
- `frontend/.env.local` (copy from `frontend/.env.local.example`)

Double-check with `git status` that neither `.env` file shows up as trackable before
your first commit.

## 1. How the Hunar integration works (implemented against the real API)

Per `https://api.voice.hunar.ai/docs/external/`, this is a two-step flow, not a
single "trigger call" call:

1. **Create an Agent** (`POST /agents/`) — a reusable voice persona + prompt +
   `result_schema`. One agent is created automatically per Screening (and per
   Reachout search) at creation time, in `hunar_client.create_agent()`. The job
   description and questions are baked into the agent's `agent_prompt` as static
   text (since Hunar's per-call `custom_data` is for small dynamic values, not a
   whole prompt).
2. **Create Calls** (`POST /calls/`) against that `agent_id`, one per candidate,
   with `callback_config.call_summary_callback_url` pointing at our webhook —
   `hunar_client.trigger_call()`.

If agent creation fails when you first create a screening/search (bad key, Hunar
down, etc.), the screening/search is still saved, and the dashboard shows a
"Retry agent creation" button that hits `POST /screenings/{id}/create-agent` (or
the `/reachout/{id}/create-agent` equivalent).

**Important limitation to know about:** Hunar's API does **not** return a raw
transcript. What you get back once a call completes is a `recording_url` (the
call audio) and a structured `result` object built from the `result_schema` you
defined on the agent. This app asks the agent to fill `answer_1`, `answer_2`...
matching your questions in order, and the dashboard zips them back together by
index — see `build_result_schema()` / `build_result_prompt()` in
`hunar_client.py` if you want to change that scheme.

**Webhook signature verification is implemented** (`app/services/webhook_security.py`,
wired into `webhook.py`): every incoming webhook is checked against
`X-Hunar-Signature` / `X-Hunar-Timestamp` over the raw request body, using your
`HUNAR_API_KEY` as the signing key, before anything touches the database. Requests
with a missing/invalid signature or a stale timestamp (>300s clock skew) get a
plain 401 and are never processed. If your org has more than one active API key,
list the extra ones in `HUNAR_WEBHOOK_API_KEYS` (comma-separated) — `HUNAR_API_KEY`
itself is always trusted automatically.

One consequence worth knowing: since real signatures require your real
`HUNAR_API_KEY`, you can't easily hand-craft a test webhook with curl/Postman
without also computing a matching signature. Easiest way to test end-to-end is
just placing a real call (see section 6) — Hunar signs it correctly for you.

**Still worth adding if this goes past the assignment:**
- Guardrails / retry_config on calls (Hunar supports auto-retry and call-time
  windows — worth adding to `trigger_call()` if you want it, they're optional
  fields Hunar defaults sensibly without).

## 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: paste your HUNAR_API_KEY, and an APOLLO_API_KEY or PDL_API_KEY
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive API docs (FastAPI auto-generates
this — useful for testing each endpoint directly before wiring up the frontend).

**Webhook callback in local dev:** Hunar needs to reach your webhook over the public
internet, so `localhost:8000` alone won't work for real test calls. Use a tunnel:

```bash
ngrok http 8000
# then set PUBLIC_BACKEND_URL in backend/.env to the printed https://*.ngrok-free.app URL
```

## 3. Frontend setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
# set NEXT_PUBLIC_API_URL to your backend URL (http://localhost:8000 locally)
npm run dev
```

Visit `http://localhost:3000`.

The `components/ui/*` files included are minimal hand-written equivalents of the
shadcn components used (button, card, input, textarea, label, badge, table) so the
app runs immediately. To get the actual shadcn CLI-managed versions (recommended
before submitting, since the brief asks for shadcn/ui specifically):

```bash
npx shadcn@latest init
npx shadcn@latest add button card input textarea label badge table
```
Answer "yes" to overwrite when prompted — the CLI output is functionally a superset
of what's here.

## 4. Try it end to end

**Project 1 — Screenings:**
1. Go to `/screenings`, create a screening with a title + JD.
2. Open it, add a candidate (name + phone in E.164 format, e.g. `+91XXXXXXXXXX`).
3. Click "Trigger calls for all candidates."
4. Once Hunar posts back to your webhook, the status flips to `completed` and you can
   view the transcript/answers/summary.

**Project 2 — Reachout:**
1. Go to `/reachout`, paste a JD, optionally override the location.
2. This calls your people-search provider and lands you on a results page.
3. Click "Reach out to all" to trigger voice calls to the matched candidates.
4. Same webhook/dashboard pattern as above.

## 5. Deployment

- **Frontend → Vercel:** import the repo, set root directory to `frontend/`, add
  `NEXT_PUBLIC_API_URL` as an env var pointing at your deployed backend.
- **Backend → Render or Railway** (needs a long-running server, not serverless, since
  it receives webhooks): root directory `backend/`, build command
  `pip install -r requirements.txt`, start command
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Add all the `.env` values as
  environment variables in the platform's dashboard — never in the repo.
  Set `PUBLIC_BACKEND_URL` to the deployed backend's own URL, and `FRONTEND_ORIGIN`
  to the deployed frontend's URL (for CORS).
- **Database:** swap `DATABASE_URL` to a hosted Postgres (Neon or Supabase both have
  free tiers) for anything beyond local testing — SQLite is fine for local dev but
  won't persist reliably on most PaaS free tiers.

## 6. What's genuinely done vs. what needs your finishing pass

Done: full DB schema, both API flows end-to-end against the real Hunar Agents +
Calls + Webhooks API, agent auto-creation with a retry affordance, webhook
receiver matching the real `call_summary` payload, polling dashboard UI with
recording playback and zipped question/answer results, JD→questions and
JD→search-criteria LLM helper (with a non-LLM fallback so it runs without an
extra key).

Needs your pass, given the 3-day window:
- Pick and fully wire one people-search provider (Apollo.io is recommended for
  phone-number coverage) — test with a real API key, since Apollo's `people/match`
  reveal-phone-number step is a separate billed call from search.
- CSV bulk-upload for candidates in Project 1, if you want it beyond one-at-a-time.
- Basic auth/login if you want the dashboard non-public in production (not included —
  currently anyone with the URL can view/trigger calls).
- `result_schema`/answers currently key by position (`answer_1`, `answer_2`...).
  Fine for this assignment's scale; if questions ever get reordered on an existing
  screening after calls have already gone out, older stored answers will
  misalign with the new question list — not an issue unless you edit questions
  mid-flight.
