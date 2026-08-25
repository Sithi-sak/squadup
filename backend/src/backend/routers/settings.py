from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status

from ..core.auth import get_current_user_id
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/settings", tags=["settings"])


# Schemas ---------------------------------------------------------------------------------


class PaymentCardOut(CamelModel):
    id: str
    brand: str
    label: str
    detail: str | None
    is_default: bool


class SessionOut(CamelModel):
    id: str
    device: str | None
    location: str | None
    last_active_at: str
    is_current: bool


# Payment cards -----------------------------------------------------------------------------
# Read/manage only, per `SettingsPaymentsTab.vue`'s "+ Add card" - it's a disabled stub with no
# card-capture form (real tokenization is Phase 4), so rows only ever get seeded directly
# (3.13d's smoke test), never created through this router.


def _get_owned_card(user_id: str, card_id: str) -> dict:
    result = (
        get_supabase_client()
        .table("payment_cards")
        .select("*")
        .eq("id", card_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment card not found")
    return result.data


@router.get("/payment-cards", response_model=list[PaymentCardOut])
def list_payment_cards(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    return (
        get_supabase_client()
        .table("payment_cards")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
        .data
        or []
    )


@router.patch("/payment-cards/{card_id}/default", response_model=PaymentCardOut)
def set_default_payment_card(card_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    _get_owned_card(user_id, card_id)
    client = get_supabase_client()
    client.table("payment_cards").update({"is_default": False}).eq("user_id", user_id).execute()
    client.table("payment_cards").update({"is_default": True}).eq("id", card_id).execute()
    return _get_owned_card(user_id, card_id)


@router.delete("/payment-cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_card(card_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    _get_owned_card(user_id, card_id)
    get_supabase_client().table("payment_cards").delete().eq("id", card_id).execute()


# Active sessions -----------------------------------------------------------------------------
# `active_sessions` (2.3) has no write path from anywhere else, so unlike payment cards (seeded
# only for the 3.13d smoke test) this router owns the one real write: `POST /settings/sessions`
# upserts the caller's own device row from its `User-Agent`, meant to be called on frontend auth
# init (3.13g) so the list reflects real logins instead of staying empty for every real account.
# `location` stays null - no IP-geolocation service is wired (per the 2.4 storage-buckets note on
# leaving unbuilt-upload columns null ahead of the feature that fills them).


def _parse_device(user_agent: str | None) -> str:
    ua = user_agent or ""
    if "Edg/" in ua:
        browser = "Edge"
    elif "OPR/" in ua or "Opera" in ua:
        browser = "Opera"
    elif "Firefox/" in ua:
        browser = "Firefox"
    elif "Chrome/" in ua:
        browser = "Chrome"
    elif "Safari/" in ua:
        browser = "Safari"
    else:
        browser = "Unknown browser"

    if "iPhone" in ua or "iPad" in ua:
        os_name = "iOS"
    elif "Android" in ua:
        os_name = "Android"
    elif "Mac OS X" in ua:
        os_name = "macOS"
    elif "Windows" in ua:
        os_name = "Windows"
    elif "Linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Unknown device"

    return f"{browser} · {os_name}"


def _get_owned_session(user_id: str, session_id: str) -> dict:
    result = (
        get_supabase_client()
        .table("active_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return result.data


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    return (
        get_supabase_client()
        .table("active_sessions")
        .select("*")
        .eq("user_id", user_id)
        .order("last_active_at", desc=True)
        .execute()
        .data
        or []
    )


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def touch_session(
    user_id: str = Depends(get_current_user_id),
    user_agent: str | None = Header(default=None),
) -> dict:
    device = _parse_device(user_agent)
    client = get_supabase_client()

    existing = (
        client.table("active_sessions")
        .select("id")
        .eq("user_id", user_id)
        .eq("device", device)
        .maybe_single()
        .execute()
    )
    client.table("active_sessions").update({"is_current": False}).eq("user_id", user_id).execute()

    if existing and existing.data:
        session_id = existing.data["id"]
        client.table("active_sessions").update(
            {"last_active_at": datetime.now(UTC).isoformat(), "is_current": True}
        ).eq("id", session_id).execute()
    else:
        inserted = (
            client.table("active_sessions")
            .insert({"user_id": user_id, "device": device, "is_current": True})
            .execute()
        )
        session_id = inserted.data[0]["id"]

    return _get_owned_session(user_id, session_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    _get_owned_session(user_id, session_id)
    get_supabase_client().table("active_sessions").delete().eq("id", session_id).execute()


@router.post("/sessions/sign-out-others", response_model=list[SessionOut])
def sign_out_other_sessions(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    client = get_supabase_client()
    client.table("active_sessions").delete().eq("user_id", user_id).eq("is_current", False).execute()
    return client.table("active_sessions").select("*").eq("user_id", user_id).execute().data or []
