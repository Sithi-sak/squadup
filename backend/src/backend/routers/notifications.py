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
    thread_id: str | None = None


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
def mark_all_read(
    exclude_type: str | None = None, user_id: str = Depends(get_current_user_id)
) -> None:
    """`exclude_type` leaves one kind untouched - the header dropdown passes `message`, since
    chat lives on the messages button's own badge and is cleared by opening the thread."""
    query = (
        get_supabase_client()
        .table("notifications")
        .update({"read": True})
        .eq("user_id", user_id)
        .eq("read", False)
    )
    if exclude_type:
        query = query.neq("type", exclude_type)
    query.execute()


@router.post("/threads/{thread_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_thread_read(thread_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    """Opening a conversation clears its chat alerts. Message notifications never reach the
    header dropdown, so this is what retires them."""
    (
        get_supabase_client()
        .table("notifications")
        .update({"read": True})
        .eq("user_id", user_id)
        .eq("type", "message")
        .eq("thread_id", thread_id)
        .execute()
    )


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


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_notification(notification_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    """Per-row dismiss in the header dropdown. Scoped by `user_id` so a guessed id from another
    account deletes nothing (the service-role client bypasses RLS, as everywhere in this file)."""
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

    (
        client.table("notifications")
        .delete()
        .eq("id", notification_id)
        .eq("user_id", user_id)
        .execute()
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_notifications(
    exclude_type: str | None = None, user_id: str = Depends(get_current_user_id)
) -> None:
    """The dropdown's "Clear" - empties the caller's notification list outright. Read state is
    irrelevant here: clearing is the user saying they are done with all of it. `exclude_type`
    spares one kind, as on `read-all`."""
    query = get_supabase_client().table("notifications").delete().eq("user_id", user_id)
    if exclude_type:
        query = query.neq("type", exclude_type)
    query.execute()
