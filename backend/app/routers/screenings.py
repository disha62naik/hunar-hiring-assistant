# from datetime import datetime
# from fastapi import APIRouter, Depends, HTTPException
# from sqlmodel import Session, select

# from app.database import get_session
# from app.models import Screening, Candidate, Call, CallStatus
# from app.schemas import ScreeningCreate, CandidateBulkCreate
# from app.services.llm_service import generate_questions
# from app.services.hunar_client import hunar_client
# from app.config import settings

# router = APIRouter(prefix="/screenings", tags=["screenings"])


# @router.post("")
# async def create_screening(body: ScreeningCreate, session: Session = Depends(get_session)):
#     questions = body.questions or await generate_questions(body.job_description)

#     screening = Screening(title=body.title, job_description=body.job_description, questions=questions)
#     session.add(screening)
#     session.commit()
#     session.refresh(screening)

#     # Create the Hunar agent for this screening now, so trigger-calls later
#     # doesn't have to. Stored on the screening; if this fails (bad API key,
#     # Hunar downtime), the screening still exists -- retry by calling
#     # POST /screenings/{id}/create-agent (below) once the issue is fixed.
#     try:
#         agent = await hunar_client.create_agent(
#             name=screening.title,
#             job_description=screening.job_description,
#             questions=questions,
#             purpose="You are screening an inbound candidate who applied for this role.",
#             objective=f"Screen candidates for the {screening.title} role and capture their answers.",
#         )
#         screening.hunar_agent_id = agent["id"]
#         session.add(screening)
#         session.commit()
#         session.refresh(screening)
#     except Exception as e:  # noqa: BLE001
#         # Don't fail screening creation over an agent-creation hiccup --
#         # surface it so the frontend can show a retry affordance.
#         return {**screening.model_dump(), "agent_error": str(e)}

#     return screening


# @router.post("/{screening_id}/create-agent")
# async def retry_create_agent(screening_id: int, session: Session = Depends(get_session)):
#     """Retry creating the Hunar agent if it failed at screening-creation time."""
#     screening = session.get(Screening, screening_id)
#     if not screening:
#         raise HTTPException(404, "Screening not found")
#     agent = await hunar_client.create_agent(
#         name=screening.title,
#         job_description=screening.job_description,
#         questions=screening.questions,
#         purpose="You are screening an inbound candidate who applied for this role.",
#         objective=f"Screen candidates for the {screening.title} role and capture their answers.",
#     )
#     screening.hunar_agent_id = agent["id"]
#     session.add(screening)
#     session.commit()
#     session.refresh(screening)
#     return screening


# @router.get("")
# def list_screenings(session: Session = Depends(get_session)):
#     return session.exec(select(Screening).order_by(Screening.created_at.desc())).all()


# @router.get("/{screening_id}")
# def get_screening(screening_id: int, session: Session = Depends(get_session)):
#     screening = session.get(Screening, screening_id)
#     if not screening:
#         raise HTTPException(404, "Screening not found")
#     candidates = session.exec(
#         select(Candidate).where(Candidate.screening_id == screening_id)
#     ).all()
#     result = []
#     for c in candidates:
#         latest_call = session.exec(
#             select(Call).where(Call.candidate_id == c.id).order_by(Call.created_at.desc())
#         ).first()
#         result.append({"candidate": c, "call": latest_call})
#     return {"screening": screening, "candidates": result}


# @router.post("/{screening_id}/candidates")
# def add_candidates(screening_id: int, body: CandidateBulkCreate, session: Session = Depends(get_session)):
#     screening = session.get(Screening, screening_id)
#     if not screening:
#         raise HTTPException(404, "Screening not found")
#     created = []
#     for c in body.candidates:
#         candidate = Candidate(screening_id=screening_id, name=c.name, phone=c.phone, email=c.email)
#         session.add(candidate)
#         created.append(candidate)
#     session.commit()
#     for c in created:
#         session.refresh(c)
#     return created


# @router.post("/{screening_id}/trigger-calls")
# async def trigger_calls(screening_id: int, session: Session = Depends(get_session)):
#     screening = session.get(Screening, screening_id)
#     if not screening:
#         raise HTTPException(404, "Screening not found")
#     if not screening.hunar_agent_id:
#         raise HTTPException(
#             400,
#             "No Hunar agent exists for this screening yet -- call "
#             f"POST /screenings/{screening_id}/create-agent first.",
#         )

#     candidates = session.exec(
#         select(Candidate).where(Candidate.screening_id == screening_id)
#     ).all()

#     webhook_url = f"{settings.public_backend_url}/webhook/hunar"

#     triggered = []
#     for candidate in candidates:
#         call = Call(candidate_id=candidate.id, status=CallStatus.pending)
#         session.add(call)
#         session.commit()
#         session.refresh(call)

#         request_id = f"screening-{screening_id}-candidate-{candidate.id}"
#         try:
#             resp = await hunar_client.trigger_call(
#                 agent_id=screening.hunar_agent_id,
#                 phone=candidate.phone,
#                 candidate_name=candidate.name,
#                 webhook_url=webhook_url,
#                 request_id=request_id,
#             )
#             call.hunar_call_id = resp["id"]
#             call.request_id = resp.get("request_id", request_id)
#             call.status = CallStatus(resp.get("status", "NOT_STARTED"))
#         except Exception as e:  # noqa: BLE001
#             call.status = CallStatus.failed
#             call.error_message = str(e)

#         session.add(call)
#         session.commit()
#         triggered.append(call)

#     return triggered


from datetime import datetime
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Screening, Candidate, Call, CallStatus
from app.schemas import ScreeningCreate, CandidateBulkCreate
from app.services.llm_service import generate_questions
from app.services.hunar_client import hunar_client
from app.config import settings

router = APIRouter(prefix="/screenings", tags=["screenings"])


@router.post("")
async def create_screening(body: ScreeningCreate, session: Session = Depends(get_session)):
    questions = body.questions or await generate_questions(body.job_description)

    screening = Screening(title=body.title, job_description=body.job_description, questions=questions)
    session.add(screening)
    session.commit()
    session.refresh(screening)

    # Create the Hunar agent for this screening now, so trigger-calls later
    # doesn't have to. Stored on the screening; if this fails (bad API key,
    # Hunar downtime), the screening still exists -- retry by calling
    # POST /screenings/{id}/create-agent (below) once the issue is fixed.
    try:
        agent = await hunar_client.create_agent(
            name=screening.title,
            job_description=screening.job_description,
            questions=questions,
            purpose="You are screening an inbound candidate who applied for this role.",
            objective=f"Screen candidates for the {screening.title} role and capture their answers.",
        )
        screening.hunar_agent_id = agent["id"]
        session.add(screening)
        session.commit()
        session.refresh(screening)
    except httpx.HTTPStatusError as e:
        return {**screening.model_dump(), "agent_error": f"Hunar rejected agent creation: {e.response.text}"}
    except Exception as e:  # noqa: BLE001
        return {**screening.model_dump(), "agent_error": str(e)}

    return screening


@router.post("/{screening_id}/create-agent")
async def retry_create_agent(screening_id: int, session: Session = Depends(get_session)):
    """Retry creating the Hunar agent if it failed at screening-creation time."""
    screening = session.get(Screening, screening_id)
    if not screening:
        raise HTTPException(404, "Screening not found")
    try:
        agent = await hunar_client.create_agent(
            name=screening.title,
            job_description=screening.job_description,
            questions=screening.questions,
            purpose="You are screening an inbound candidate who applied for this role.",
            objective=f"Screen candidates for the {screening.title} role and capture their answers.",
        )
    except httpx.HTTPStatusError as e:
        # Surface Hunar's actual rejection message instead of a bare 500.
        raise HTTPException(e.response.status_code, f"Hunar rejected agent creation: {e.response.text}")
    screening.hunar_agent_id = agent["id"]
    session.add(screening)
    session.commit()
    session.refresh(screening)
    return screening


@router.get("")
def list_screenings(session: Session = Depends(get_session)):
    return session.exec(select(Screening).order_by(Screening.created_at.desc())).all()


@router.get("/{screening_id}")
def get_screening(screening_id: int, session: Session = Depends(get_session)):
    screening = session.get(Screening, screening_id)
    if not screening:
        raise HTTPException(404, "Screening not found")
    candidates = session.exec(
        select(Candidate).where(Candidate.screening_id == screening_id)
    ).all()
    result = []
    for c in candidates:
        latest_call = session.exec(
            select(Call).where(Call.candidate_id == c.id).order_by(Call.created_at.desc())
        ).first()
        result.append({"candidate": c, "call": latest_call})
    return {"screening": screening, "candidates": result}


@router.post("/{screening_id}/candidates")
def add_candidates(screening_id: int, body: CandidateBulkCreate, session: Session = Depends(get_session)):
    screening = session.get(Screening, screening_id)
    if not screening:
        raise HTTPException(404, "Screening not found")
    created = []
    for c in body.candidates:
        candidate = Candidate(screening_id=screening_id, name=c.name, phone=c.phone, email=c.email)
        session.add(candidate)
        created.append(candidate)
    session.commit()
    for c in created:
        session.refresh(c)
    return created


@router.post("/{screening_id}/trigger-calls")
async def trigger_calls(screening_id: int, session: Session = Depends(get_session)):
    screening = session.get(Screening, screening_id)
    if not screening:
        raise HTTPException(404, "Screening not found")
    if not screening.hunar_agent_id:
        raise HTTPException(
            400,
            "No Hunar agent exists for this screening yet -- call "
            f"POST /screenings/{screening_id}/create-agent first.",
        )

    candidates = session.exec(
        select(Candidate).where(Candidate.screening_id == screening_id)
    ).all()

    webhook_url = f"{settings.public_backend_url}/webhook/hunar"

    triggered = []
    for candidate in candidates:
        call = Call(candidate_id=candidate.id, status=CallStatus.pending)
        session.add(call)
        session.commit()
        session.refresh(call)

        request_id = f"screening-{screening_id}-candidate-{candidate.id}"
        try:
            resp = await hunar_client.trigger_call(
                agent_id=screening.hunar_agent_id,
                phone=candidate.phone,
                candidate_name=candidate.name,
                webhook_url=webhook_url,
                request_id=request_id,
            )
            call.hunar_call_id = resp["id"]
            call.request_id = resp.get("request_id", request_id)
            call.status = CallStatus(resp.get("status", "NOT_STARTED"))
        except Exception as e:  # noqa: BLE001
            call.status = CallStatus.failed
            call.error_message = str(e)

        session.add(call)
        session.commit()
        triggered.append(call)

    return triggered