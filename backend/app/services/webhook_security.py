"""
Verifies X-Hunar-Signature / X-Hunar-Timestamp on incoming Hunar webhooks,
straight from Hunar's "Webhook Signature Validation" docs page.

Signed message = "{timestamp}." + raw JSON body bytes, HMAC-SHA256 with your
Hunar API key, base64-encoded. Hunar may send multiple comma-separated
signatures if your org has more than one active API key -- verification
passes if any signature matches any trusted key.
"""
import base64
import hashlib
import hmac
import time
from collections.abc import Iterable

WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS = 300


def compute_hunar_signature(*, api_key: str, request_body: bytes, timestamp: str) -> str:
    message = f"{timestamp.strip()}.".encode("utf-8") + request_body
    digest = hmac.new(api_key.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def verify_hunar_webhook_signature(
    *,
    signature_header: str | None,
    timestamp_header: str | None,
    request_body: bytes,
    trusted_api_keys: Iterable[str],
) -> bool:
    if not (signature_header and signature_header.strip()):
        return False
    if not (timestamp_header and timestamp_header.strip()):
        return False

    # Reject stale/replayed timestamps -- outside a 300s window of our clock.
    try:
        ts = int(timestamp_header.strip())
    except ValueError:
        return False
    if abs(time.time() - ts) > WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS:
        return False

    timestamp = timestamp_header.strip()
    signatures = [s.strip() for s in signature_header.split(",") if s.strip()]
    trusted = [k for k in trusted_api_keys if k]  # drop empty/unset keys
    if not signatures or not trusted:
        return False

    for api_key in trusted:
        computed = compute_hunar_signature(api_key=api_key, request_body=request_body, timestamp=timestamp)
        for signature in signatures:
            if hmac.compare_digest(signature, computed):
                return True
    return False
