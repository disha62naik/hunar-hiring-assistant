# Testing checklist

Work through this top to bottom. Each stage assumes the previous one passed.

## Stage 0 — Environment sanity

- [ ] `backend/.env` has real values for `HUNAR_API_KEY` and `APOLLO_API_KEY` (or `PDL_API_KEY` + `PEOPLE_SEARCH_PROVIDER=pdl`).
- [ ] `uvicorn app.main:app --reload --port 8000` starts with no traceback.
- [ ] `http://localhost:8000/` returns `{"status": "ok"}`.
- [ ] `http://localhost:8000/docs` loads the Swagger UI and lists all routes
      (`/screenings`, `/reachout`, `/calls`, `/webhook/hunar`).
- [ ] `npm run dev` starts the frontend with no build errors, `http://localhost:3000`
      loads the two-card home page.

## Stage 1 — Hunar auth works at all (before any of your own logic)

Test this directly in `/docs` (Swagger UI) before going through your own UI —
it isolates "is my API key valid" from "is my app's logic correct."

- [ ] `GET /agents/` via Swagger → **expect 200** with a list (probably empty first time).
      If you get 401 here, your `HUNAR_API_KEY` is wrong before anything else matters.
- [ ] `GET /numbers/` (if you added this route — it's documented but not
      wired into this app since it wasn't needed for the flow; test it directly
      against Hunar with curl if you want to confirm what `from_phone_number`
      options you have):
  ```bash
  curl https://api.voice.hunar.ai/external/v1/numbers/ -H "X-API-Key: $HUNAR_API_KEY"
  ```

## Stage 2 — Project 1: Screening, happy path

1. [ ] `/screenings` → create a screening with a real short JD (e.g. "Field Sales
       Executive, Bangalore, 2+ years FMCG experience"). Submit.
2. [ ] You land back on the list with the new screening. Click into it.
3. [ ] **No red "agent didn't get created" banner appears.** If it does, click
       "Retry agent creation" and watch the Network tab / backend terminal for
       the actual error message from Hunar (usually a validation error naming
       the bad field).
4. [ ] Add yourself as a candidate: your real name, your real phone in
       `+91XXXXXXXXXX` format.
5. [ ] Click "Trigger calls for all candidates." Status badge should move from
       grey (`pending`/`NOT_STARTED`) toward `RINGING` within a few seconds.
6. [ ] **Answer the call on your phone.** Have a short real conversation —
       answer 2-3 of the questions the agent asks.
7. [ ] Hang up. Within ~5-30 seconds (webhook delivery + your 5s poll interval),
       the badge should flip to `COMPLETED`.
8. [ ] Click "View results." Confirm:
   - [ ] Duration shown is roughly what the real call lasted.
   - [ ] The recording `<audio>` player loads and plays back your actual call.
   - [ ] At least some of the question/answer pairs match what you actually said.
       (Answers being imperfect paraphrases is normal — an LLM is summarizing
       your speech; totally blank or totally wrong answers means the
       `result_prompt`/`result_schema` wiring needs a look.)

## Stage 3 — Project 1: expected failure paths

- [ ] Add a candidate with an obviously malformed phone number (e.g. `12345`,
      missing `+countrycode`). Trigger calls. That candidate's call should end
      up `FAILED` with `error_message` populated — check via
      `GET /calls/{id}` in Swagger — rather than crashing the whole batch.
- [ ] Add a candidate with a real number that you **do not answer**. Confirm it
      eventually lands on `NOT_CONNECTED`, not stuck on `RINGING` forever.
- [ ] Trigger calls on a screening with zero candidates — button should already
      be disabled (candidates.length === 0), confirm you can't click it.

## Stage 4 — Project 2: People Search & Reachout, happy path

1. [ ] `/reachout` → paste a real JD with a clear title, e.g. "Senior Backend
       Engineer, Python, Bangalore."
2. [ ] Submit. You should land on the results page with a list of candidates
       (name, title, company) pulled from your configured provider.
   - [ ] If the list is empty: check the backend terminal — Apollo's free tier
         commonly returns matches but 0 phone numbers if you've exhausted
         reveal credits, and this app silently skips candidates with no phone
         (`if not p.get("phone"): continue` in `reachout.py`). That's expected
         behavior, not a bug, but worth knowing so you don't chase a phantom
         issue.
3. [ ] No "agent didn't get created" banner (or use Retry if it appears).
4. [ ] Click "Reach out to all" — same call-status flow as Stage 2. For a real
       test, temporarily edit one candidate's row in the DB (or add yourself
       manually via `POST /reachout/search`'s underlying candidate table — easiest
       is just to test with a search where you know your own number appears,
       or directly insert yourself via the `/docs` Swagger UI against a raw
       SQL/DB tool) so you have a real number to answer and verify end-to-end.

## Stage 5 — Webhook signature verification

You can't easily hand-craft a fake webhook without your real API key (that's
the point), so verify it two ways:

- [ ] **Positive proof**: every completed call in Stages 2/4 above updated the
      dashboard. Since `webhook.py` now rejects unsigned/invalid requests with
      401 *before* writing to the DB, a status flipping to `COMPLETED` is itself
      proof a validly-signed webhook was accepted.
- [ ] **Negative proof** (optional but reassuring): hit your own webhook URL
      with a plain curl POST and no signature headers — confirm you get 401,
      not 200:
  ```bash
  curl -i -X POST https://<your-ngrok-or-render-url>/webhook/hunar \
    -H "Content-Type: application/json" \
    -d '{"event_type":"call_summary","call_id":"fake","status":"COMPLETED"}'
  ```
  Expected: `HTTP/1.1 401 Unauthorized`, and nothing changes in your DB.

## Stage 6 — Frontend UI checks (no real calls needed)

- [ ] Home page: both cards link correctly to `/screenings` and `/reachout`.
- [ ] Screening create form: submitting with empty title/JD is blocked by the
      `required` HTML attribute (browser-level validation).
- [ ] Screening detail page auto-refreshes every 5s (watch Network tab for
      repeated `GET /screenings/{id}` calls) without you touching anything.
- [ ] Badge colors are sensible: grey for not-started, amber/yellow for
      in-progress states, green for `COMPLETED`, red for `FAILED`/`NOT_CONNECTED`.

## Stage 7 — Deployment smoke test (after Render + Vercel are live)

- [ ] Deployed frontend URL loads without console errors (check browser devtools).
- [ ] Creating a screening on the deployed frontend actually reaches the deployed
      backend (Network tab shows requests going to your Render URL, not
      `localhost`).
- [ ] `PUBLIC_BACKEND_URL` on Render is set to Render's own URL (not the old
      ngrok one) — otherwise Hunar's webhook will try to call a dead ngrok
      tunnel and your production calls will never show as `COMPLETED`.
- [ ] Repeat one real call test (Stage 2, steps 4-8) against the deployed URLs
      before you submit — this is the single most important check, since it's
      the exact path your assignment reviewer will exercise.
