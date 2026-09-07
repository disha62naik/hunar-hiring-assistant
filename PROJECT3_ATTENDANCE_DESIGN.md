# Project 3 — Tracking attendance for 1000 people across 100 locations, no smartphones, LLMs exist

## Constraint check
"No smartphones" doesn't mean no phones or no connectivity — feature phones,
landlines, and shared devices are assumed to still exist, since only "apps" and
smartphones are ruled out. That reframes the problem: track attendance without an
app on each person's own device.

## Core idea: one shared voice touchpoint per location, not one device per person

Each of the 100 locations gets a single phone number (or a shared landline/kiosk
handset) connected to an LLM-driven IVR (interactive voice response) system —
functionally similar to what Hunar itself does for hiring calls, but for attendance.

**Check-in/check-out flow per employee, per shift:**
1. Employee calls (or is called by) the location's number at shift start.
2. The LLM greets them, asks for their employee ID, and a short rotating
   verification phrase or a personal onboarding-profile question to reduce buddy
   punching (e.g. "what's your supervisor's first name").
3. The LLM logs name, ID, location, and timestamp to a central attendance database.
4. Repeat at shift end for check-out; the LLM computes hours worked automatically.

## Handling scale (1000 people, 100 locations)
- Average ~10 people per location — a single shared line per site can handle this
  as sequential short calls at shift boundaries (staggered by role/shift, not everyone
  calling at once).
- For sites without individual phone access, a **supervisor-mediated roll call**:
  the LLM voice-interviews the site supervisor once per day ("read me who's absent
  and who's present"), and the LLM parses that into per-employee records. This covers
  workers with zero personal phone access.

## What the LLM actually does (its real value-add here)
- Runs a natural, multilingual conversational IVR that tolerates noisy environments,
  accents, and interruptions far better than rigid touch-tone menus.
- Parses free-form speech into structured records (name, ID, timestamp, location).
- Cross-checks for anomalies: same voice/ID claiming two locations same day, missing
  checkouts, patterns of lateness — and flags only the exceptions.
- Generates a daily digest for HR: attendance %, exceptions, location-level trends —
  so no one has to manually read 1000 rows a day across 100 sites.

## Fallbacks / edge cases
- No phone access at all: a physical sign-in sheet at the site, photographed or
  read aloud by the supervisor to the LLM at day's end.
- Poor connectivity: SMS-based check-in as a backup channel (still no app needed),
  parsed by the same LLM pipeline.
- Fraud resistance: rotating challenge phrases + supervisor spot-checks, rather than
  biometrics (out of scope without smartphones/dedicated hardware).

## Why not [alternative]
- RFID/badge readers per site: works, but is a hardware procurement problem across
  100 locations, and doesn't use "LLMs exist" as the given advantage — voice does.
- A call center handling all 1000 people manually: doesn't scale without automation;
  the LLM is what makes one line per site viable instead of needing 100 human
  operators.
