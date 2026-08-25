from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import get_current_user_id
from ..core.notify import notify
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/messages", tags=["messages"])


# Schemas ---------------------------------------------------------------------------------


class StartThreadIn(CamelModel):
    participant_id: str


class SendMessageIn(CamelModel):
    body: str


class ThreadOut(CamelModel):
    id: str
    participant_id: str
    participant_display_name: str
    last_message_preview: str | None
    updated_at: str
    unread_count: int


class MessageOut(CamelModel):
    id: str
    thread_id: str
    sender_id: str
    body: str
    created_at: str


# Helpers -----------------------------------------------------------------------------------

_THREAD_SELECT = (
    "id, user_a_id, user_b_id, created_at, "
    "user_a:users!message_threads_user_a_id_fkey(display_name), "
    "user_b:users!message_threads_user_b_id_fkey(display_name)"
)


def _canonical_pair(user_id: str, participant_id: str) -> tuple[str, str]:
    """`message_threads` has one row per unordered pair (CHECKPOINT.md's Messages note), but its
    unique constraint is on the ordered `(user_a_id, user_b_id)` tuple - sorting the ids keeps
    every thread between the same two people stored (and found) under one canonical row
    regardless of who started it."""
    return (user_id, participant_id) if user_id < participant_id else (participant_id, user_id)


def _get_thread(client, thread_id: str, user_id: str) -> dict:
    result = client.table("message_threads").select(_THREAD_SELECT).eq("id", thread_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found")
    thread = result.data
    if user_id not in (thread["user_a_id"], thread["user_b_id"]):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found")
    return thread


def _thread_out(thread: dict, user_id: str, *, last_message: dict | None, unread_count: int) -> dict:
    is_a = thread["user_a_id"] == user_id
    participant_id = thread["user_b_id"] if is_a else thread["user_a_id"]
    participant = (thread.get("user_b") if is_a else thread.get("user_a")) or {}
    return {
        "id": thread["id"],
        "participant_id": participant_id,
        "participant_display_name": participant.get("display_name") or "SquadUp user",
        "last_message_preview": last_message["body"] if last_message else None,
        "updated_at": last_message["created_at"] if last_message else thread["created_at"],
        "unread_count": unread_count,
    }


# Routes --------------------------------------------------------------------------------------


@router.get("/threads", response_model=list[ThreadOut])
def list_threads(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    """Messages page's thread list. One inbox per account (CHECKPOINT.md's Messages note), so
    this covers both a plain user's and a Pal's view with no persona split."""
    client = get_supabase_client()
    threads = (
        client.table("message_threads")
        .select(_THREAD_SELECT)
        .or_(f"user_a_id.eq.{user_id},user_b_id.eq.{user_id}")
        .execute()
        .data
        or []
    )
    if not threads:
        return []

    thread_ids = [t["id"] for t in threads]
    messages = (
        client.table("messages")
        .select("id, thread_id, sender_id, body, read_at, created_at")
        .in_("thread_id", thread_ids)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )

    last_message_by_thread: dict[str, dict] = {}
    unread_by_thread: dict[str, int] = {}
    for message in messages:
        last_message_by_thread.setdefault(message["thread_id"], message)
        if message["sender_id"] != user_id and message["read_at"] is None:
            unread_by_thread[message["thread_id"]] = unread_by_thread.get(message["thread_id"], 0) + 1

    out = [
        _thread_out(
            thread,
            user_id,
            last_message=last_message_by_thread.get(thread["id"]),
            unread_count=unread_by_thread.get(thread["id"], 0),
        )
        for thread in threads
    ]
    out.sort(key=lambda t: t["updated_at"], reverse=True)
    return out


@router.post("/threads", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
def start_thread(payload: StartThreadIn, user_id: str = Depends(get_current_user_id)) -> dict:
    if payload.participant_id == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot start a thread with yourself")

    client = get_supabase_client()
    participant = client.table("users").select("id").eq("id", payload.participant_id).maybe_single().execute()
    if not participant or not participant.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    user_a_id, user_b_id = _canonical_pair(user_id, payload.participant_id)
    existing = (
        client.table("message_threads")
        .select(_THREAD_SELECT)
        .eq("user_a_id", user_a_id)
        .eq("user_b_id", user_b_id)
        .maybe_single()
        .execute()
    )
    if existing and existing.data:
        thread = existing.data
    else:
        created = (
            client.table("message_threads")
            .insert({"user_a_id": user_a_id, "user_b_id": user_b_id})
            .execute()
        )
        thread = _get_thread(client, created.data[0]["id"], user_id)

    return _thread_out(thread, user_id, last_message=None, unread_count=0)


@router.get("/threads/{thread_id}/messages", response_model=list[MessageOut])
def list_messages(thread_id: str, user_id: str = Depends(get_current_user_id)) -> list[dict]:
    """Opening a thread also marks the other party's unread messages read, replacing the
    frontend-only `unreadCount = 0` `stores/messages.ts` previously did on `selectThread`."""
    client = get_supabase_client()
    _get_thread(client, thread_id, user_id)

    rows = (
        client.table("messages")
        .select("id, thread_id, sender_id, body, created_at")
        .eq("thread_id", thread_id)
        .order("created_at")
        .execute()
        .data
        or []
    )

    client.table("messages").update({"read_at": datetime.now(UTC).isoformat()}).eq("thread_id", thread_id).neq(
        "sender_id", user_id
    ).is_("read_at", "null").execute()

    return rows


@router.post(
    "/threads/{thread_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
def send_message(thread_id: str, payload: SendMessageIn, user_id: str = Depends(get_current_user_id)) -> dict:
    body = payload.body.strip()
    if not body:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Message body cannot be empty")

    client = get_supabase_client()
    thread = _get_thread(client, thread_id, user_id)

    created = (
        client.table("messages")
        .insert({"thread_id": thread_id, "sender_id": user_id, "body": body})
        .execute()
    )

    is_a = thread["user_a_id"] == user_id
    sender = (thread.get("user_a") if is_a else thread.get("user_b")) or {}
    sender_name = sender.get("display_name") or "Someone"
    other_user_id = thread["user_b_id"] if is_a else thread["user_a_id"]
    preview = body if len(body) <= 60 else f"{body[:57]}..."
    notify(other_user_id, "message", f'{sender_name} sent you a message: "{preview}"')

    return created.data[0]
