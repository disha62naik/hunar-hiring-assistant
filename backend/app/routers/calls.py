from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.models import Call

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("/{call_id}")
def get_call(call_id: int, session: Session = Depends(get_session)):
    call = session.get(Call, call_id)
    if not call:
        raise HTTPException(404, "Call not found")
    return call
