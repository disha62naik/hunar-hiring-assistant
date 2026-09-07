from typing import Optional, List
from pydantic import BaseModel


# ---------- Screenings ----------

class ScreeningCreate(BaseModel):
    title: str
    job_description: str
    # optional manual question list; if omitted, questions are auto-generated from the JD
    questions: Optional[List[str]] = None


class CandidateCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None


class CandidateBulkCreate(BaseModel):
    candidates: List[CandidateCreate]


# ---------- Reachout ----------

class ReachoutSearchCreate(BaseModel):
    job_description: str
    location: Optional[str] = None
    max_results: int = 20


# ---------- Webhook ----------
# Documents the real shape of Hunar's `call_summary` event for reference.
# webhook.py reads the raw JSON body directly rather than validating against
# this model, since Hunar's payload includes several fields we don't use.

class HunarWebhookPayload(BaseModel):
    event_type: str
    call_id: str
    agent_id: str
    request_id: Optional[str] = None
    status: str
    lifecycle_status: Optional[str] = None
    recording_url: Optional[str] = None
    result: Optional[dict] = None
    duration_seconds: Optional[float] = None
