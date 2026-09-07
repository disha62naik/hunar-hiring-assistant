from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON


class CandidateSource(str, Enum):
    manual = "manual"
    people_search = "people_search"


class CallStatus(str, Enum):
    """Mirrors Hunar's `status` values on the Call resource, plus our own
    local-only `pending` for a Call row created before Hunar has been called."""
    pending = "pending"
    not_started = "NOT_STARTED"
    scheduled = "SCHEDULED"
    initiated = "INITIATED"
    ringing = "RINGING"
    in_progress = "IN_PROGRESS"
    completed = "COMPLETED"
    not_connected = "NOT_CONNECTED"
    cancelled = "CANCELLED"
    failed = "FAILED"


# ---------- Project 1: Screenings ----------

class Screening(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    job_description: str
    # list[str] of screening questions asked by the voice agent
    questions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    # the Hunar agent created for this screening (see services/hunar_client.py)
    hunar_agent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Candidate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    screening_id: Optional[int] = Field(default=None, foreign_key="screening.id")
    # Project 2 candidates are tied to a ReachoutSearch instead
    reachout_search_id: Optional[int] = Field(default=None, foreign_key="reachoutsearch.id")

    name: str
    phone: str
    email: Optional[str] = None
    title: Optional[str] = None          # job title, useful for reachout candidates
    company: Optional[str] = None
    source: CandidateSource = CandidateSource.manual
    # raw profile payload from the people-search API, kept for reference
    raw_profile: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)


class Call(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id")

    hunar_call_id: Optional[str] = None
    request_id: Optional[str] = None
    status: CallStatus = CallStatus.pending

    # Hunar does not expose a raw transcript over the API -- only a recording
    # URL (audio) and a structured `result` object (per the agent's
    # result_schema). `answers` below is populated from that `result` object;
    # keys are answer_1, answer_2... in the same order as Screening.questions
    # / ReachoutSearch.reachout_questions, since result_schema keys are
    # generated that way in hunar_client.build_result_schema().
    recording_url: Optional[str] = None
    answers: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    duration_seconds: Optional[float] = None
    # our own note when triggering the call itself fails (network error, 4xx from
    # Hunar, etc) -- distinct from any data Hunar sends back
    error_message: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------- Project 2: People Search & Reachout ----------

class ReachoutSearch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_description: str
    # criteria extracted from the JD (title, skills, location, seniority)
    criteria: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    reachout_questions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    hunar_agent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
