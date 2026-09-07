# from fastapi import APIRouter, Depends, HTTPException
# from sqlmodel import Session, select

# from app.database import get_session
# from app.models import ReachoutSearch, Candidate, Call, CallStatus, CandidateSource
# from app.schemas import ReachoutSearchCreate
# from app.services.llm_service import extract_search_criteria, generate_questions
# from app.services.people_search import search_people
# from app.services.hunar_client import hunar_client
# from app.config import settings

# router = APIRouter(prefix="/reachout", tags=["reachout"])


# @router.post("/search")
# async def create_search(body: ReachoutSearchCreate, session: Session = Depends(get_session)):
#     criteria = await extract_search_criteria(body.job_description)
#     if body.location:
#         criteria["location"] = body.location

#     questions = await generate_questions(body.job_description, n=4)

#     search = ReachoutSearch(
#         job_description=body.job_description,
#         criteria=criteria,
#         reachout_questions=questions,
#     )
#     session.add(search)
#     session.commit()
#     session.refresh(search)

#     # Create the Hunar agent for this reachout search up front, same as
#     # screenings -- questions/JD are fixed per search, so one agent covers
#     # every candidate found by it.
#     role_title = (criteria.get("titles") or ["this role"])[0]
#     try:
#         agent = await hunar_client.create_agent(
#             name=f"Reachout: {role_title}"[:64],
#             job_description=body.job_description,
#             questions=questions,
#             purpose="You are cold-calling a potential candidate about an open role, not someone who applied.",
#             objective=f"Gauge interest and qualify candidates for the {role_title} role.",
#         )
#         search.hunar_agent_id = agent["id"]
#         session.add(search)
#         session.commit()
#         session.refresh(search)
#     except Exception as e:  # noqa: BLE001
#         pass  # candidates can still be searched; retry-create-agent before triggering calls

#     people = await search_people(criteria, max_results=body.max_results)

#     candidates = []
#     for p in people:
#         if not p.get("phone"):
#             continue  # skip results with no reachable phone number
#         candidate = Candidate(
#             reachout_search_id=search.id,
#             name=p.get("name") or "Unknown",
#             phone=p["phone"],
#             email=p.get("email"),
#             title=p.get("title"),
#             company=p.get("company"),
#             source=CandidateSource.people_search,
#             raw_profile=p.get("raw_profile"),
#         )
#         session.add(candidate)
#         candidates.append(candidate)
#     session.commit()
#     for c in candidates:
#         session.refresh(c)

#     return {"search": search, "candidates": candidates}


# @router.post("/{search_id}/create-agent")
# async def retry_create_agent(search_id: int, session: Session = Depends(get_session)):
#     search = session.get(ReachoutSearch, search_id)
#     if not search:
#         raise HTTPException(404, "Search not found")
#     role_title = (search.criteria or {}).get("titles", ["this role"])[0]
#     agent = await hunar_client.create_agent(
#         name=f"Reachout: {role_title}"[:64],
#         job_description=search.job_description,
#         questions=search.reachout_questions,
#         purpose="You are cold-calling a potential candidate about an open role, not someone who applied.",
#         objective=f"Gauge interest and qualify candidates for the {role_title} role.",
#     )
#     search.hunar_agent_id = agent["id"]
#     session.add(search)
#     session.commit()
#     session.refresh(search)
#     return search


# @router.get("/{search_id}")
# def get_search(search_id: int, session: Session = Depends(get_session)):
#     search = session.get(ReachoutSearch, search_id)
#     if not search:
#         raise HTTPException(404, "Search not found")
#     candidates = session.exec(
#         select(Candidate).where(Candidate.reachout_search_id == search_id)
#     ).all()
#     result = []
#     for c in candidates:
#         latest_call = session.exec(
#             select(Call).where(Call.candidate_id == c.id).order_by(Call.created_at.desc())
#         ).first()
#         result.append({"candidate": c, "call": latest_call})
#     return {"search": search, "candidates": result}


# @router.post("/{search_id}/trigger-calls")
# async def trigger_reachout_calls(search_id: int, session: Session = Depends(get_session)):
#     search = session.get(ReachoutSearch, search_id)
#     if not search:
#         raise HTTPException(404, "Search not found")
#     if not search.hunar_agent_id:
#         raise HTTPException(
#             400,
#             "No Hunar agent exists for this search yet -- call "
#             f"POST /reachout/{search_id}/create-agent first.",
#         )

#     candidates = session.exec(
#         select(Candidate).where(Candidate.reachout_search_id == search_id)
#     ).all()

#     webhook_url = f"{settings.public_backend_url}/webhook/hunar"

#     triggered = []
#     for candidate in candidates:
#         call = Call(candidate_id=candidate.id, status=CallStatus.pending)
#         session.add(call)
#         session.commit()
#         session.refresh(call)

#         request_id = f"reachout-{search_id}-candidate-{candidate.id}"
#         try:
#             resp = await hunar_client.trigger_call(
#                 agent_id=search.hunar_agent_id,
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

from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlmodel import Session, select

from app.database import get_session
from app.models import ReachoutSearch, Candidate, Call, CallStatus, CandidateSource
from app.schemas import ReachoutSearchCreate
from app.services.llm_service import extract_search_criteria, generate_questions
from app.services.people_search import search_people
from app.services.hunar_client import hunar_client
from app.config import settings

router = APIRouter(prefix="/reachout", tags=["reachout"])


@router.post("/search")
async def create_search(body: ReachoutSearchCreate, session: Session = Depends(get_session)):
    criteria = await extract_search_criteria(body.job_description)
    if body.location:
        criteria["location"] = body.location

    questions = await generate_questions(body.job_description, n=4)

    search = ReachoutSearch(
        job_description=body.job_description,
        criteria=criteria,
        reachout_questions=questions,
    )
    session.add(search)
    session.commit()
    session.refresh(search)

    # Create the Hunar agent for this reachout search up front, same as
    # screenings -- questions/JD are fixed per search, so one agent covers
    # every candidate found by it.
    role_title = (criteria.get("titles") or ["this role"])[0]
    try:
        agent = await hunar_client.create_agent(
            name=f"Reachout: {role_title}"[:64],
            job_description=body.job_description,
            questions=questions,
            purpose="You are cold-calling a potential candidate about an open role, not someone who applied.",
            objective=f"Gauge interest and qualify candidates for the {role_title} role.",
        )
        search.hunar_agent_id = agent["id"]
        session.add(search)
        session.commit()
        session.refresh(search)
    except Exception as e:  # noqa: BLE001
        pass  # candidates can still be searched; retry-create-agent before triggering calls

    people = await search_people(criteria, max_results=body.max_results)

    candidates = []
    for p in people:
        if not p.get("phone"):
            continue  # skip results with no reachable phone number
        candidate = Candidate(
            reachout_search_id=search.id,
            name=p.get("name") or "Unknown",
            phone=p["phone"],
            email=p.get("email"),
            title=p.get("title"),
            company=p.get("company"),
            source=CandidateSource.people_search,
            raw_profile=p.get("raw_profile"),
        )
        session.add(candidate)
        candidates.append(candidate)
    session.commit()
    for c in candidates:
        session.refresh(c)

        session.refresh(search)
    return {"search": search, "candidates": candidates}


@router.post("/{search_id}/create-agent")
async def retry_create_agent(search_id: int, session: Session = Depends(get_session)):
    search = session.get(ReachoutSearch, search_id)
    if not search:
        raise HTTPException(404, "Search not found")
    role_title = (search.criteria or {}).get("titles", ["this role"])[0]
    try:
        agent = await hunar_client.create_agent(
            name=f"Reachout: {role_title}"[:64],
            job_description=search.job_description,
            questions=search.reachout_questions,
            purpose="You are cold-calling a potential candidate about an open role, not someone who applied.",
            objective=f"Gauge interest and qualify candidates for the {role_title} role.",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, f"Hunar rejected agent creation: {e.response.text}")
    search.hunar_agent_id = agent["id"]
    session.add(search)
    session.commit()
    session.refresh(search)
    return search


@router.get("/{search_id}")
def get_search(search_id: int, session: Session = Depends(get_session)):
    search = session.get(ReachoutSearch, search_id)
    if not search:
        raise HTTPException(404, "Search not found")
    candidates = session.exec(
        select(Candidate).where(Candidate.reachout_search_id == search_id)
    ).all()
    result = []
    for c in candidates:
        latest_call = session.exec(
            select(Call).where(Call.candidate_id == c.id).order_by(Call.created_at.desc())
        ).first()
        result.append({"candidate": c, "call": latest_call})
    return {"search": search, "candidates": result}


@router.post("/{search_id}/trigger-calls")
async def trigger_reachout_calls(search_id: int, session: Session = Depends(get_session)):
    search = session.get(ReachoutSearch, search_id)
    if not search:
        raise HTTPException(404, "Search not found")
    if not search.hunar_agent_id:
        raise HTTPException(
            400,
            "No Hunar agent exists for this search yet -- call "
            f"POST /reachout/{search_id}/create-agent first.",
        )

    candidates = session.exec(
        select(Candidate).where(Candidate.reachout_search_id == search_id)
    ).all()

    webhook_url = f"{settings.public_backend_url}/webhook/hunar"

    triggered = []
    for candidate in candidates:
        call = Call(candidate_id=candidate.id, status=CallStatus.pending)
        session.add(call)
        session.commit()
        session.refresh(call)

        request_id = f"reachout-{search_id}-candidate-{candidate.id}"
        try:
            resp = await hunar_client.trigger_call(
                agent_id=search.hunar_agent_id,
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