from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import get_current_user_id
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/notifications", tags=["notifications"])


# Schemas ---------------------------------------------------------------------------------


class NotificationOut(CamelModel):
    id: str
    type: str
    message: str
    read: bool
    created_at: str


# Routes --------------------------------------------------------------------------------------


@router.get("", response_model=list[NotificationOut])
def list_notifications(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    """Header dropdown + `/notifications` page. Rows are created by `core/notify.py`, called from
    bookings/messages/reviews/wallet on the events named in CHECKPOINT.md's 3.10 line."""
    return (
        get_supabase_client()
        .table("notifications")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(user_id: str = Depends(get_current_user_id)) -> None:
    get_supabase_client().table("notifications").update({"read": True}).eq("user_id", user_id).eq(
        "read", False
    ).execute()


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    existing = (
        client.table("notifications")
        .select("id")
        .eq("id", notification_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not existing or not existing.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")

    client.table("notifications").update({"read": True}).eq("id", notification_id).execute()
    return client.table("notifications").select("*").eq("id", notification_id).single().execute().data
