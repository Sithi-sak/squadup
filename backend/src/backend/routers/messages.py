from datetime import UTC, datetime
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from ..core.auth import get_current_user_id
from ..core.blocks import require_not_blocked
from ..core.notify import notify
from ..core.schema import CamelModel
from ..core.storage import upload_image_as_webp
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/messages", tags=["messages"])

#: How many messages a conversation opens with. Older ones come back page by page through
#: `before`, so opening a long-running chat costs one bounded read instead of the whole history.
_MESSAGE_PAGE_SIZE = 40
_MAX_MESSAGE_PAGE_SIZE = 100


# Schemas ---------------------------------------------------------------------------------


class StartThreadIn(CamelModel):
    participant_id: str


class MuteThreadIn(CamelModel):
    muted: bool


class MuteThreadOut(CamelModel):
    id: str
    muted: bool


class ThreadOut(CamelModel):
    id: str
    participant_id: str
    participant_display_name: str
    last_message_preview: str | None
    updated_at: str
    unread_count: int
    muted: bool


class MessageOut(CamelModel):
    id: str
    thread_id: str
    sender_id: str
    body: str
    image_url: str | None = None
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


def _preview(body: str | None, image_url: str | None) -> str | None:
    """An image-only message stores an empty `body` (20260920090000), so the inbox line needs
    something to show for it."""
    if body:
        return body
    return "Photo" if image_url else None


def _thread_out(
    thread: dict, user_id: str, *, last_message: dict | None, unread_count: int, muted: bool = False
) -> dict:
    is_a = thread["user_a_id"] == user_id
    participant_id = thread["user_b_id"] if is_a else thread["user_a_id"]
    participant = (thread.get("user_b") if is_a else thread.get("user_a")) or {}
    return {
        "id": thread["id"],
        "participant_id": participant_id,
        "participant_display_name": participant.get("display_name") or "SquadUp user",
        "last_message_preview": _preview(
            last_message["body"] if last_message else None,
            (last_message or {}).get("image_url"),
        ),
        "updated_at": last_message["created_at"] if last_message else thread["created_at"],
        "unread_count": unread_count,
        "muted": muted,
    }


def _get_thread_state(client, thread_id: str, user_id: str) -> dict:
    result = (
        client.table("message_thread_states")
        .select("muted, deleted_at")
        .eq("thread_id", thread_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    return (result.data if result else None) or {"muted": False, "deleted_at": None}


def _set_thread_state(client, thread_id: str, user_id: str, **fields) -> None:
    client.table("message_thread_states").upsert(
        {"thread_id": thread_id, "user_id": user_id, **fields},
        on_conflict="thread_id,user_id",
    ).execute()


def _require_membership(client, thread_id: str, user_id: str) -> None:
    """Cheaper than `_get_thread` for endpoints that only need the auth check, not the joined
    display names - mute/delete don't return a full `ThreadOut`, so there's no reason to pay for
    that join."""
    result = (
        client.table("message_threads")
        .select("user_a_id, user_b_id")
        .eq("id", thread_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found")
    if user_id not in (result.data["user_a_id"], result.data["user_b_id"]):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found")


# Routes --------------------------------------------------------------------------------------


@router.get("/threads", response_model=list[ThreadOut])
def list_threads(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    """Messages page's thread list. One inbox per account (CHECKPOINT.md's Messages note), so
    this covers both a plain user's and a Pal's view with no persona split.

    The whole list - participants, last message, unread tallies, mute flags, and the deleted and
    blocked filtering - comes back from `message_thread_summaries` in one round-trip (4.49). It
    used to be four, the last of which read every message in every one of the viewer's threads
    just to keep the newest of each.
    """
    client = get_supabase_client()
    rows = client.rpc("message_thread_summaries", {"p_user_id": user_id}).execute().data or []
    return [
        {
            "id": row["id"],
            "participant_id": row["participant_id"],
            "participant_display_name": row["participant_display_name"] or "SquadUp user",
            "last_message_preview": _preview(row["last_message_body"], row["last_message_image_url"]),
            "updated_at": row["updated_at"],
            "unread_count": row["unread_count"],
            "muted": row["muted"],
        }
        for row in rows
    ]


@router.post("/threads", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
def start_thread(payload: StartThreadIn, user_id: str = Depends(get_current_user_id)) -> dict:
    if payload.participant_id == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot start a thread with yourself")

    client = get_supabase_client()
    participant = client.table("users").select("id").eq("id", payload.participant_id).maybe_single().execute()
    if not participant or not participant.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    require_not_blocked(user_id, payload.participant_id, "message")

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
        # Starting a thread you'd previously deleted brings it back into your list rather than
        # leaving it permanently hidden - matches `_get_thread_state`'s "no row = not deleted".
        state = _get_thread_state(client, thread["id"], user_id)
        if state["deleted_at"]:
            _set_thread_state(client, thread["id"], user_id, deleted_at=None)
    else:
        created = (
            client.table("message_threads")
            .insert({"user_a_id": user_a_id, "user_b_id": user_b_id})
            .execute()
        )
        thread = _get_thread(client, created.data[0]["id"], user_id)
        state = {"muted": False}

    return _thread_out(thread, user_id, last_message=None, unread_count=0, muted=state["muted"])


@router.get("/threads/{thread_id}/messages", response_model=list[MessageOut])
def list_messages(
    thread_id: str,
    background: BackgroundTasks,
    limit: int = Query(_MESSAGE_PAGE_SIZE, ge=1, le=_MAX_MESSAGE_PAGE_SIZE),
    before: str | None = Query(None, description="ISO timestamp - returns messages older than this"),
    user_id: str = Depends(get_current_user_id),
) -> list[dict]:
    """A page of the conversation, newest `limit` first from the database but returned oldest
    first so the caller can render it straight down the transcript. `before` walks backwards
    through the history for "Load earlier messages" (4.49) - the endpoint used to return every
    message in the thread, so a long chat paid for all of it on every open.

    Opening a thread also marks the other party's unread messages read, replacing the
    frontend-only `unreadCount = 0` `stores/messages.ts` previously did on `selectThread`. That
    UPDATE is nothing the response depends on, so it runs after the response is sent rather than
    holding the transcript behind a write.
    """
    client = get_supabase_client()
    _require_membership(client, thread_id, user_id)

    query = (
        client.table("messages")
        .select("id, thread_id, sender_id, body, image_url, created_at")
        .eq("thread_id", thread_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    if before:
        query = query.lt("created_at", before)
    rows = query.execute().data or []

    if not before:
        background.add_task(_mark_thread_read, thread_id, user_id)

    rows.reverse()
    return rows


def _mark_thread_read(thread_id: str, user_id: str) -> None:
    get_supabase_client().table("messages").update({"read_at": datetime.now(UTC).isoformat()}).eq(
        "thread_id", thread_id
    ).neq("sender_id", user_id).is_("read_at", "null").execute()


@router.post(
    "/threads/{thread_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    thread_id: str,
    body: str = Form(""),
    image: UploadFile | None = File(None),  # noqa: B008
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Multipart rather than JSON (4.49) so an attached image rides along as a real file, same
    shape as the feed composer's `POST /feed/posts`. It is re-encoded to WebP and downscaled by
    `upload_image_as_webp` before it lands in the `message-images` bucket, on top of the
    downscale the client already does - a multi-MB phone photo has no business being stored at
    full size for a chat bubble. Either the text or the image may be missing, not both."""
    body = body.strip()
    if not body and image is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Message must have text or an image")

    client = get_supabase_client()
    thread = _get_thread(client, thread_id, user_id)
    other_id = thread["user_b_id"] if thread["user_a_id"] == user_id else thread["user_a_id"]
    require_not_blocked(user_id, other_id, "message")

    image_url = (
        upload_image_as_webp("message-images", f"{user_id}/{uuid4()}", image) if image else None
    )

    created = (
        client.table("messages")
        .insert({"thread_id": thread_id, "sender_id": user_id, "body": body, "image_url": image_url})
        .execute()
    )

    is_a = thread["user_a_id"] == user_id
    sender = (thread.get("user_a") if is_a else thread.get("user_b")) or {}
    sender_name = sender.get("display_name") or "Someone"
    other_user_id = thread["user_b_id"] if is_a else thread["user_a_id"]
    if body:
        preview = body if len(body) <= 60 else f"{body[:57]}..."
        message = f'{sender_name} sent you a message: "{preview}"'
    else:
        message = f"{sender_name} sent you a photo"
    notify(other_user_id, "message", message, thread_id=thread_id)

    # A new message un-hides the thread for whoever deleted it, so it isn't lost off their list
    # forever - mirrors `start_thread`'s own revive-on-restart behavior.
    _set_thread_state(client, thread_id, other_user_id, deleted_at=None)

    return created.data[0]


@router.patch("/threads/{thread_id}/mute", response_model=MuteThreadOut)
def set_thread_muted(
    thread_id: str, payload: MuteThreadIn, user_id: str = Depends(get_current_user_id)
) -> dict:
    client = get_supabase_client()
    _require_membership(client, thread_id, user_id)
    _set_thread_state(client, thread_id, user_id, muted=payload.muted)
    return {"id": thread_id, "muted": payload.muted}


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(thread_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    """Hides the thread from this user's list only - the other participant's copy (and the
    messages themselves) are untouched, per `message_thread_states`' per-user design."""
    client = get_supabase_client()
    _require_membership(client, thread_id, user_id)
    _set_thread_state(client, thread_id, user_id, deleted_at=datetime.now(UTC).isoformat())
