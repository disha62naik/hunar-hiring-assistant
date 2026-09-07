import json
from fastapi import APIRouter, Depends, Request, Response
from sqlmodel import Session, select

from app.database import get_session
from app.models import Call, CallStatus
from app.config import settings
from app.services.webhook_security import verify_hunar_webhook_signature

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/hunar")
async def hunar_webhook(request: Request, session: Session = Depends(get_session)):
    """
    Receives Hunar's `call_summary` event (set as call_summary_callback_url in
    callback_config when the call was created) -- fired once when a call's
    lifecycle reaches a terminal state (COMPLETED, FAILED, CANCELLED,
    NOT_CONNECTED). Payload combines status + recording_url + result.

    Verifies X-Hunar-Signature / X-Hunar-Timestamp over the raw body BEFORE
    touching the database, per Hunar's "Webhook Signature Validation" docs.
    """
    raw_body = await request.body()

    verified = verify_hunar_webhook_signature(
        signature_header=request.headers.get("X-Hunar-Signature"),
        timestamp_header=request.headers.get("X-Hunar-Timestamp"),
        request_body=raw_body,
        trusted_api_keys=settings.hunar_trusted_webhook_keys,
    )
    if not verified:
        # Invalid/missing signature or stale timestamp -- reject before any
        # DB write. 401 per Hunar's own example (views.py in their docs).
        return Response(status_code=401)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return Response(status_code=400)

    call_id = payload.get("call_id")
    if not call_id:
        return {"ok": False, "error": "missing call_id in payload"}

    call = session.exec(
        select(Call).where(Call.hunar_call_id == call_id)
    ).first()
    if not call:
        return {"ok": False, "error": f"no matching call for {call_id}"}

    # idempotency: if we've already recorded this call as terminal, don't
    # reprocess (Hunar may redeliver the same webhook on retry)
    if call.status in (CallStatus.completed, CallStatus.failed, CallStatus.cancelled, CallStatus.not_connected):
        return {"ok": True, "note": "already processed"}

    raw_status = payload.get("status")
    if raw_status:
        try:
            call.status = CallStatus(raw_status)
        except ValueError:
            pass  # unrecognized status string -- leave call.status as-is

    call.recording_url = payload.get("recording_url", call.recording_url)
    call.answers = payload.get("result", call.answers)
    call.duration_seconds = payload.get("duration_seconds", call.duration_seconds)

    session.add(call)
    session.commit()
    return {"ok": True}
