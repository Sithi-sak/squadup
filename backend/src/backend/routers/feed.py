import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import Field

from ..core import video as clips
from ..core.auth import get_current_user_id, get_optional_user_id
from ..core.blocks import blocked_user_ids, require_not_blocked
from ..core.schema import CamelModel
from ..core.storage import upload_bytes, upload_image_as_webp
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/feed", tags=["feed"])

logger = logging.getLogger(__name__)


# Schemas ---------------------------------------------------------------------------------


class PostOut(CamelModel):
    id: str
    author_id: str
    author: str
    handle: str | None
    tier: str | None
    player_id: str | None
    avatar_url: str | None
    online: bool
    text: str | None
    has_image: bool
    image_url: str | None
    image_urls: list[str]
    video_url: str | None
    video_poster_url: str | None
    video_status: str | None
    category: str
    tag: str | None
    kind: str
    likes: int
    comments: int
    liked: bool
    following: bool
    created_at: str


class CommentCreateIn(CamelModel):
    text: str
    parent_comment_id: str | None = None


class CommentOut(CamelModel):
    id: str
    post_id: str
    author_id: str
    author: str
    avatar_url: str | None = None
    parent_comment_id: str | None
    text: str
    likes: int
    liked: bool
    is_creator: bool
    created_at: str
    replies: list["CommentOut"] = Field(default_factory=list)


class FollowOut(CamelModel):
    followed_id: str
    following: bool
    followers_count: int


class FollowUserOut(CamelModel):
    id: str
    display_name: str
    handle: str | None
    avatar_url: str | None
    tier: str | None
    following: bool


class SavedItemIn(CamelModel):
    kind: str
    post_id: str | None = None
    service_id: str | None = None


class SavedItemOut(CamelModel):
    id: str
    kind: str
    created_at: str
    post_id: str | None = None
    author_id: str | None = None
    author: str | None = None
    avatar_url: str | None = None
    handle: str | None = None
    tier: str | None = None
    text: str | None = None
    has_image: bool | None = None
    likes: int | None = None
    comments: int | None = None
    service_id: str | None = None
    name: str | None = None
    by: str | None = None
    category: str | None = None
    price_coins: int | None = None
    price_unit: str | None = None
    promo_label: str | None = None
    player_id: str | None = None


# Helpers -----------------------------------------------------------------------------------

_MAX_POST_IMAGES = 10

_POST_SELECT = "*"
_COMMENT_SELECT = "*, users!comments_author_id_fkey(display_name)"
_SAVED_SELECT = (
    "*, posts(*), "
    "services(*, players!services_player_id_fkey(display_name), service_pricing_options(*), service_promotions(*))"
)


def _get_post(client, post_id: str) -> dict:
    result = client.table("posts").select(_POST_SELECT).eq("id", post_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return result.data


def _resolve_authors(client, author_ids: set[str]) -> tuple[dict[str, dict], dict[str, dict]]:
    """Batch-resolves post/comment author display info for a set of user ids - same
    "aggregate in Python" convention `_serialize_posts`'s `liked_ids`/`following_ids` already use.
    Any signed-in user can be an author now (3.18), so this always looks up `users` for the
    display name/handle (4.14 - one handle for every account, not just Pals) and separately looks
    up `players` (may be absent - a plain buyer has no Pal profile) for the tier/avatar/online
    fields."""
    if not author_ids:
        return {}, {}
    ids = list(author_ids)
    users_by_id = {
        u["id"]: u
        for u in client.table("users").select("id, display_name, handle").in_("id", ids).execute().data or []
    }
    players_by_user_id = {
        p["user_id"]: p
        for p in client.table("players")
        .select("id, user_id, tier, avatar_url, online")
        .in_("user_id", ids)
        .execute()
        .data
        or []
    }
    return users_by_id, players_by_user_id


def _resolve_author(client, author_id: str | None) -> tuple[dict | None, dict | None]:
    if not author_id:
        return None, None
    users_by_id, players_by_user_id = _resolve_authors(client, {author_id})
    return users_by_id.get(author_id), players_by_user_id.get(author_id)


def _collect_uploads(image: UploadFile | None, images: list[UploadFile] | None) -> list[UploadFile]:
    """Multipart clients send either the single legacy `image` field or a repeated `images` one;
    an empty repeated field arrives as a one-item list with no filename, which is not a file."""
    candidates = ([image] if image else []) + list(images or [])
    return [upload for upload in candidates if upload and upload.filename][:_MAX_POST_IMAGES]


# A clip still `processing` after this long lost its encode (the server restarted mid-job, the
# worker died), so it reads as `failed` and its author can delete it and try again.
_VIDEO_STALE_AFTER = timedelta(minutes=30)


def _video_status(row: dict) -> str | None:
    video_status = row.get("video_status")
    if video_status == "processing":
        created_at = datetime.fromisoformat(row["created_at"])
        if datetime.now(UTC) - created_at > _VIDEO_STALE_AFTER:
            return "failed"
    return video_status


def _visible_posts(rows: list[dict], viewer_id: str | None) -> list[dict]:
    """Drops clips that aren't ready yet unless the viewer wrote them: everyone else only sees a
    video post once there is a video to play."""
    return [row for row in rows if row.get("video_status") in (None, "ready") or row["author_id"] == viewer_id]


def _finish_post_video(post_id: str, src: Path, info: clips.VideoInfo) -> None:
    """Runs on the encode worker after `create_post` has already answered: encodes the clip,
    stores it and its poster, and flips the post to `ready`, or to `failed` if anything breaks.
    A post deleted while it waited in the queue is skipped rather than uploaded for nothing."""
    client = get_supabase_client()
    try:
        post = client.table("posts").select("author_id").eq("id", post_id).maybe_single().execute()
        if not post or not post.data:
            return
        encoded = clips.encode_clip(src, info)
        key = f"{post.data['author_id']}/{uuid4()}"
        video_url = upload_bytes("post-videos", f"{key}.mp4", encoded.video, "video/mp4")
        poster_url = upload_bytes("post-images", f"{key}.webp", encoded.poster, "image/webp")
        client.table("posts").update(
            {"video_url": video_url, "video_poster_url": poster_url, "video_status": "ready"}
        ).eq("id", post_id).execute()
    except Exception:
        logger.exception("Encoding the clip for post %s failed", post_id)
        client.table("posts").update({"video_status": "failed"}).eq("id", post_id).execute()
    finally:
        src.unlink(missing_ok=True)


def _post_out(row: dict, author: dict | None, player: dict | None, *, liked: bool, following: bool) -> dict:
    author = author or {}
    player = player or {}
    return {
        "id": row["id"],
        "author_id": row["author_id"],
        "author": author.get("display_name") or "SquadUp user",
        "handle": author.get("handle"),
        "tier": player.get("tier"),
        "player_id": player.get("id"),
        "avatar_url": player.get("avatar_url"),
        "online": bool(player.get("online")),
        "text": row["text"],
        "has_image": row["image_url"] is not None,
        "image_url": row["image_url"],
        "image_urls": row.get("image_urls") or ([row["image_url"]] if row["image_url"] else []),
        "video_url": row.get("video_url"),
        "video_poster_url": row.get("video_poster_url"),
        "video_status": _video_status(row),
        "category": row["category"],
        "tag": row.get("tag"),
        "kind": row["kind"],
        "likes": row["likes_count"],
        "comments": row["comments_count"],
        "liked": liked,
        "following": following,
        "created_at": row["created_at"],
    }


def _serialize_posts(client, rows: list[dict], viewer_id: str | None) -> list[dict]:
    if not rows:
        return []
    author_ids = {r["author_id"] for r in rows}
    users_by_id, players_by_user_id = _resolve_authors(client, author_ids)

    liked_ids: set[str] = set()
    following_ids: set[str] = set()
    if viewer_id:
        post_ids = [r["id"] for r in rows]
        liked_ids = {
            like["post_id"]
            for like in client.table("post_likes")
            .select("post_id")
            .eq("user_id", viewer_id)
            .in_("post_id", post_ids)
            .execute()
            .data
            or []
        }
        following_ids = {
            f["followed_id"]
            for f in client.table("follows")
            .select("followed_id")
            .eq("follower_id", viewer_id)
            .in_("followed_id", list(author_ids))
            .execute()
            .data
            or []
        }
    return [
        _post_out(
            r,
            users_by_id.get(r["author_id"]),
            players_by_user_id.get(r["author_id"]),
            liked=r["id"] in liked_ids,
            following=r["author_id"] in following_ids,
        )
        for r in rows
    ]


def _refresh_post(client, post_id: str, viewer_id: str) -> dict:
    """Recomputes and writes `likes_count` in one atomic statement (`refresh_post_likes_count`
    RPC) instead of a separate select-then-update - the old two-step version raced under
    overlapping like/unlike calls on the same post and could leave a wrong count permanently
    stored."""
    client.rpc("refresh_post_likes_count", {"target_post_id": post_id}).execute()
    row = _get_post(client, post_id)
    return _serialize_posts(client, [row], viewer_id)[0]


def _refresh_posts_count(client, author_id: str) -> None:
    count = len(client.table("posts").select("id").eq("author_id", author_id).execute().data or [])
    client.table("users").update({"posts_count": count}).eq("id", author_id).execute()


def _refresh_comments_count(client, post_id: str) -> None:
    count = len(client.table("comments").select("id").eq("post_id", post_id).execute().data or [])
    client.table("posts").update({"comments_count": count}).eq("id", post_id).execute()


def _comment_avatars(client, rows: list[dict]) -> dict[str, str | None]:
    """Comment authors' avatars live on `players` (a plain buyer has none), keyed by user id."""
    _, players_by_user_id = _resolve_authors(client, {r["author_id"] for r in rows})
    return {user_id: p.get("avatar_url") for user_id, p in players_by_user_id.items()}


def _comment_out(row: dict, *, liked: bool, creator_user_id: str | None, avatar_url: str | None = None) -> dict:
    author = (row.get("users") or {}).get("display_name") or "SquadUp user"
    return {
        "id": row["id"],
        "post_id": row["post_id"],
        "author_id": row["author_id"],
        "author": author,
        "avatar_url": avatar_url,
        "parent_comment_id": row["parent_comment_id"],
        "text": row["text"],
        "likes": row["likes_count"],
        "liked": liked,
        "is_creator": creator_user_id is not None and row["author_id"] == creator_user_id,
        "created_at": row["created_at"],
        "replies": [],
    }


def _build_comment_tree(rows: list[dict]) -> list[dict]:
    """`comments.parent_comment_id` is a flat self-reference, but `FeedComment.replies` (and the
    recursive `FeedCommentItem.vue`) expect a nested tree - rows arrive ordered by `created_at`
    so both the roots and each parent's `replies` stay chronological."""
    by_id = {r["id"]: r for r in rows}
    roots: list[dict] = []
    for row in rows:
        parent_id = row["parent_comment_id"]
        if parent_id and parent_id in by_id:
            by_id[parent_id]["replies"].append(row)
        else:
            roots.append(row)
    return roots


def _get_comment_with_creator(client, comment_id: str) -> tuple[dict, str | None]:
    result = (
        client.table("comments")
        .select(f"{_COMMENT_SELECT}, posts(author_id)")
        .eq("id", comment_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    row = result.data
    creator_user_id = (row.get("posts") or {}).get("author_id")
    return row, creator_user_id


def _refresh_comment(client, comment_id: str, *, liked: bool) -> dict:
    """Same atomic-RPC fix as `_refresh_post`, for comment likes."""
    client.rpc("refresh_comment_likes_count", {"target_comment_id": comment_id}).execute()
    row, creator_user_id = _get_comment_with_creator(client, comment_id)
    avatars = _comment_avatars(client, [row])
    return _comment_out(row, liked=liked, creator_user_id=creator_user_id, avatar_url=avatars.get(row["author_id"]))


def _refresh_follow(client, target_id: str, follower_id: str, *, following: bool) -> dict:
    followers_count = len(
        client.table("follows").select("follower_id").eq("followed_id", target_id).execute().data or []
    )
    client.table("users").update({"followers_count": followers_count}).eq("id", target_id).execute()

    following_count = len(
        client.table("follows").select("followed_id").eq("follower_id", follower_id).execute().data or []
    )
    client.table("users").update({"following_count": following_count}).eq("id", follower_id).execute()

    return {"followed_id": target_id, "following": following, "followers_count": followers_count}


def _service_promo_label(service: dict) -> str | None:
    for promo in service.get("service_promotions") or []:
        if promo.get("active"):
            return promo.get("label")
    return None


def _saved_item_out(row: dict, author: dict | None = None, player: dict | None = None) -> dict:
    base = {"id": row["id"], "kind": row["kind"], "created_at": row["created_at"]}
    if row["kind"] == "post":
        post = row.get("posts") or {}
        author = author or {}
        player = player or {}
        return {
            **base,
            "post_id": row["post_id"],
            "author_id": post.get("author_id"),
            "author": author.get("display_name"),
            "avatar_url": player.get("avatar_url"),
            "handle": author.get("handle"),
            "tier": player.get("tier"),
            "player_id": player.get("id"),
            "text": post.get("text"),
            "has_image": post.get("image_url") is not None if post else None,
            "likes": post.get("likes_count"),
            "comments": post.get("comments_count"),
        }

    service = row.get("services") or {}
    player = service.get("players") or {}
    pricing = sorted(service.get("service_pricing_options") or [], key=lambda p: p["sort_order"])
    first = pricing[0] if pricing else None
    return {
        **base,
        "service_id": row["service_id"],
        "name": service.get("name"),
        "by": player.get("display_name"),
        "category": (service.get("styles") or [None])[0],
        "price_coins": first["price_coins"] if first else None,
        "price_unit": first["price_unit"] if first else None,
        "promo_label": _service_promo_label(service),
    }


# Posts ---------------------------------------------------------------------------------------
# `/feed`, `/feed/following`, and `GET /feed/posts/{id}` stay public (browsing, per the 2.5 note)
# but personalize `liked`/`following` when a bearer token is present via `get_optional_user_id`.


@router.get("", response_model=list[PostOut])
def list_feed(
    author_id: str | None = Query(None, alias="authorId"),
    user_id: str | None = Depends(get_optional_user_id),
) -> list[dict]:
    client = get_supabase_client()
    query = client.table("posts").select(_POST_SELECT).order("created_at", desc=True).limit(50)
    if author_id:
        query = query.eq("author_id", author_id)
    rows = query.execute().data or []
    # Neither side of a block sees the other's posts (4.39). Filtered here rather than in
    # `_serialize_posts` so a direct permalink still resolves - that read has its own rules.
    blocked = blocked_user_ids(user_id)
    if blocked:
        rows = [row for row in rows if row.get("author_id") not in blocked]
    return _serialize_posts(client, _visible_posts(rows, user_id), user_id)


@router.get("/following", response_model=list[PostOut])
def list_following_feed(user_id: str | None = Depends(get_optional_user_id)) -> list[dict]:
    if not user_id:
        return []
    client = get_supabase_client()
    followed = client.table("follows").select("followed_id").eq("follower_id", user_id).execute().data or []
    blocked = blocked_user_ids(user_id)
    author_ids = [f["followed_id"] for f in followed if f["followed_id"] not in blocked]
    if not author_ids:
        return []
    rows = (
        client.table("posts")
        .select(_POST_SELECT)
        .in_("author_id", author_ids)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )
    return _serialize_posts(client, _visible_posts(rows, user_id), user_id)


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    text: str | None = Form(None),
    category: str = Form("games"),
    tag: str | None = Form(None),
    image: UploadFile | None = File(None),  # noqa: B008
    images: list[UploadFile] | None = File(None),  # noqa: B008
    video: UploadFile | None = File(None),  # noqa: B008
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """The Feed composer (`CreatePostModal.vue`) - any signed-in account can post (3.18), Pal or
    plain buyer, so this just needs the caller's own user id, no `players` lookup. Multipart
    (not JSON) so attached images can ride along as real files - each is re-encoded to WebP and
    downscaled by `upload_image_as_webp` before it lands in the `post-images` bucket, so a
    multi-MB phone photo doesn't get stored at full size for a feed-card thumbnail. `images`
    takes the whole set (up to `_MAX_POST_IMAGES`); the single `image` field predates it and
    still works, counting as one more.

    A `video` instead makes it a clip post (4.61): the upload is checked here (readable, not too
    big or long) so a bad file fails the request, then the row goes in as `processing` and
    `_finish_post_video` encodes it on the background worker. Encoding takes seconds to minutes,
    far too long to hold the request open."""
    client = get_supabase_client()

    uploads = _collect_uploads(image, images)
    has_video = bool(video and video.filename)
    clean_text = (text or "").strip() or None
    if has_video and uploads:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A post can have photos or a video, not both")
    if not clean_text and not uploads and not has_video:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Post must have text or an image")

    video_src: Path | None = None
    video_info: clips.VideoInfo | None = None
    if video and has_video:
        video_src = clips.save_upload(video)
        try:
            video_info = clips.probe(video_src)
        except BaseException:
            video_src.unlink(missing_ok=True)
            raise

    image_urls = [upload_image_as_webp("post-images", f"{user_id}/{uuid4()}", upload) for upload in uploads]

    post_id = str(uuid4())
    try:
        client.table("posts").insert(
            {
                "id": post_id,
                "author_id": user_id,
                "text": clean_text,
                "image_url": image_urls[0] if image_urls else None,
                "image_urls": image_urls,
                "category": "clips" if has_video else category,
                "tag": (tag or "").strip() or None,
                "video_status": "processing" if has_video else None,
            }
        ).execute()
    except BaseException:
        if video_src:
            video_src.unlink(missing_ok=True)
        raise
    if video_src and video_info:
        clips.submit(_finish_post_video, post_id, video_src, video_info)
    _refresh_posts_count(client, user_id)

    row = _get_post(client, post_id)
    return _serialize_posts(client, [row], user_id)[0]


@router.patch("/posts/{post_id}", response_model=PostOut)
def update_post(
    post_id: str,
    text: str = Form(""),
    image: UploadFile | None = File(None),  # noqa: B008
    images: list[UploadFile] | None = File(None),  # noqa: B008
    keep_image_urls: list[str] | None = Form(None),  # noqa: B008
    manage_images: bool = Form(False),
    remove_image: bool = Form(False),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Author-only edit - category and tag stay fixed once posted (never were editable, same as
    before), but text and images can both change. With `manage_images`, `keep_image_urls` is the
    authoritative list of existing images that survive the edit, in display order, and
    `images`/`image` is appended to it as new uploads - an empty list with no uploads clears them.
    Without it the old single-image callers still behave exactly as they used to (`image`
    replaces, `remove_image` clears, neither leaves the post's images alone)."""
    client = get_supabase_client()
    post = _get_post(client, post_id)
    if post["author_id"] != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your post")

    existing = post.get("image_urls") or ([post["image_url"]] if post["image_url"] else [])
    uploads = _collect_uploads(image, images)
    # A clip post keeps its video through an edit; only the caption changes.
    is_clip = post.get("video_status") is not None
    if is_clip and uploads:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A post can have photos or a video, not both")

    if manage_images:
        kept = [url for url in (keep_image_urls or []) if url in existing]
    elif remove_image and not uploads:
        kept = []
    elif uploads:
        kept = []  # Legacy single-image replace.
    else:
        kept = existing

    new_urls = [upload_image_as_webp("post-images", f"{user_id}/{uuid4()}", upload) for upload in uploads]
    image_urls = (kept + new_urls)[:_MAX_POST_IMAGES]

    clean_text = text.strip() or None
    if not clean_text and not image_urls and not is_clip:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Post must have text or an image")

    client.table("posts").update(
        {
            "text": clean_text,
            "image_url": image_urls[0] if image_urls else None,
            "image_urls": image_urls,
        }
    ).eq("id", post_id).execute()
    row = _get_post(client, post_id)
    return _serialize_posts(client, [row], user_id)[0]


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    """Author-only delete. Comments, likes and saved entries all cascade off the `posts` row's
    foreign keys, so the one explicit follow-up is the author's `posts_count`. Uploaded images
    and clips are left in their buckets, same as an edit that drops an image."""
    client = get_supabase_client()
    post = _get_post(client, post_id)
    if post["author_id"] != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your post")

    client.table("posts").delete().eq("id", post_id).execute()
    _refresh_posts_count(client, user_id)


@router.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: str, user_id: str | None = Depends(get_optional_user_id)) -> dict:
    client = get_supabase_client()
    row = _get_post(client, post_id)
    if not _visible_posts([row], user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return _serialize_posts(client, [row], user_id)[0]


@router.post("/posts/{post_id}/like", response_model=PostOut)
def like_post(post_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _get_post(client, post_id)
    client.table("post_likes").upsert({"user_id": user_id, "post_id": post_id}).execute()
    return _refresh_post(client, post_id, user_id)


@router.delete("/posts/{post_id}/like", response_model=PostOut)
def unlike_post(post_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _get_post(client, post_id)
    client.table("post_likes").delete().eq("user_id", user_id).eq("post_id", post_id).execute()
    return _refresh_post(client, post_id, user_id)


class PostReportIn(CamelModel):
    reason: str
    details: str | None = None


class PostReportOut(CamelModel):
    id: str
    status: str
    report_count: int


@router.post("/posts/{post_id}/report", response_model=PostReportOut, status_code=status.HTTP_201_CREATED)
def report_post(post_id: str, payload: PostReportIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """"Report post" from the feed card's "..." menu (4.77b), read by the admin panel's Reported
    posts tab (`GET /admin/post-reports`). Same collapse rule as `report_player`: one pending row
    per post and reason, bumped by each new reporter, untouched by a repeat from the same one.
    The author and text are copied onto the row so it still reads if the post is later removed."""
    reason = payload.reason.strip()
    if not reason:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A reason is required")

    client = get_supabase_client()
    post = _get_post(client, post_id)
    if not _visible_posts([post], user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post["author_id"] == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't report your own post")

    details = (payload.details or "").strip() or None

    existing = (
        client.table("post_reports")
        .select("id, report_count, details, reported_by")
        .eq("post_id", post_id)
        .eq("reason", reason)
        .eq("status", "pending")
        .limit(1)
        .execute()
        .data
        or []
    )
    if existing:
        row = existing[0]
        if row.get("reported_by") == user_id:
            return {"id": row["id"], "status": "pending", "report_count": row["report_count"]}
        update: dict = {"report_count": row["report_count"] + 1}
        if details and not row.get("details"):
            update["details"] = details
        client.table("post_reports").update(update).eq("id", row["id"]).execute()
        return {"id": row["id"], "status": "pending", "report_count": update["report_count"]}

    created = (
        client.table("post_reports")
        .insert(
            {
                "post_id": post_id,
                "author_id": post["author_id"],
                "post_text": post.get("text"),
                "reason": reason,
                "details": details,
                "reported_by": user_id,
            }
        )
        .execute()
        .data[0]
    )
    return {"id": created["id"], "status": created["status"], "report_count": created["report_count"]}


# Comments --------------------------------------------------------------------------------


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: str, user_id: str | None = Depends(get_optional_user_id)) -> list[dict]:
    client = get_supabase_client()
    post = _get_post(client, post_id)
    creator_user_id = post["author_id"]

    rows = (
        client.table("comments").select(_COMMENT_SELECT).eq("post_id", post_id).order("created_at").execute().data
        or []
    )
    liked_ids: set[str] = set()
    if user_id and rows:
        comment_ids = [r["id"] for r in rows]
        liked_ids = {
            like["comment_id"]
            for like in client.table("comment_likes")
            .select("comment_id")
            .eq("user_id", user_id)
            .in_("comment_id", comment_ids)
            .execute()
            .data
            or []
        }

    avatars = _comment_avatars(client, rows)
    out_rows = [
        _comment_out(
            r, liked=r["id"] in liked_ids, creator_user_id=creator_user_id, avatar_url=avatars.get(r["author_id"])
        )
        for r in rows
    ]
    return _build_comment_tree(out_rows)


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(post_id: str, payload: CommentCreateIn, user_id: str = Depends(get_current_user_id)) -> dict:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Comment cannot be empty")

    client = get_supabase_client()
    post = _get_post(client, post_id)
    if payload.parent_comment_id:
        parent = (
            client.table("comments")
            .select("id")
            .eq("id", payload.parent_comment_id)
            .eq("post_id", post_id)
            .maybe_single()
            .execute()
        )
        if not parent or not parent.data:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent comment not found")

    comment_id = str(uuid4())
    client.table("comments").insert(
        {
            "id": comment_id,
            "post_id": post_id,
            "author_id": user_id,
            "parent_comment_id": payload.parent_comment_id,
            "text": text,
        }
    ).execute()
    _refresh_comments_count(client, post_id)

    row = client.table("comments").select(_COMMENT_SELECT).eq("id", comment_id).single().execute().data
    creator_user_id = post["author_id"]
    avatars = _comment_avatars(client, [row])
    return _comment_out(row, liked=False, creator_user_id=creator_user_id, avatar_url=avatars.get(user_id))


@router.post("/comments/{comment_id}/like", response_model=CommentOut)
def like_comment(comment_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _get_comment_with_creator(client, comment_id)
    client.table("comment_likes").upsert({"user_id": user_id, "comment_id": comment_id}).execute()
    return _refresh_comment(client, comment_id, liked=True)


@router.delete("/comments/{comment_id}/like", response_model=CommentOut)
def unlike_comment(comment_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _get_comment_with_creator(client, comment_id)
    client.table("comment_likes").delete().eq("user_id", user_id).eq("comment_id", comment_id).execute()
    return _refresh_comment(client, comment_id, liked=False)


# Follows -----------------------------------------------------------------------------------


def _require_user_exists(client, user_id: str) -> dict:
    result = client.table("users").select("id, display_name").eq("id", user_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return result.data


@router.post("/follows/{target_id}", response_model=FollowOut)
def follow_user(target_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    """Any signed-in account can be followed now (3.18), Pal or plain buyer."""
    client = get_supabase_client()
    if target_id == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot follow yourself")
    _require_user_exists(client, target_id)
    require_not_blocked(user_id, target_id, "follow")
    client.table("follows").upsert({"follower_id": user_id, "followed_id": target_id}).execute()
    return _refresh_follow(client, target_id, user_id, following=True)


@router.delete("/follows/{target_id}", response_model=FollowOut)
def unfollow_user(target_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _require_user_exists(client, target_id)
    client.table("follows").delete().eq("follower_id", user_id).eq("followed_id", target_id).execute()
    return _refresh_follow(client, target_id, user_id, following=False)


def _follow_user_rows(client, user_ids: list[str], viewer_id: str | None) -> list[dict]:
    if not user_ids:
        return []
    users_by_id, players_by_user_id = _resolve_authors(client, set(user_ids))
    following_ids: set[str] = set()
    if viewer_id:
        following_ids = {
            f["followed_id"]
            for f in client.table("follows")
            .select("followed_id")
            .eq("follower_id", viewer_id)
            .in_("followed_id", user_ids)
            .execute()
            .data
            or []
        }
    rows = []
    for uid in user_ids:
        user = users_by_id.get(uid) or {}
        player = players_by_user_id.get(uid) or {}
        rows.append(
            {
                "id": uid,
                "display_name": user.get("display_name") or "SquadUp user",
                "handle": user.get("handle"),
                "avatar_url": player.get("avatar_url"),
                "tier": player.get("tier"),
                "following": uid in following_ids,
            }
        )
    return rows


@router.get("/follows/{user_id}/followers", response_model=list[FollowUserOut])
def list_followers(user_id: str, viewer_id: str | None = Depends(get_optional_user_id)) -> list[dict]:
    client = get_supabase_client()
    _require_user_exists(client, user_id)
    rows = (
        client.table("follows")
        .select("follower_id, created_at")
        .eq("followed_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return _follow_user_rows(client, [r["follower_id"] for r in rows], viewer_id)


@router.get("/follows/{user_id}/following", response_model=list[FollowUserOut])
def list_following_users(user_id: str, viewer_id: str | None = Depends(get_optional_user_id)) -> list[dict]:
    client = get_supabase_client()
    _require_user_exists(client, user_id)
    rows = (
        client.table("follows")
        .select("followed_id, created_at")
        .eq("follower_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return _follow_user_rows(client, [r["followed_id"] for r in rows], viewer_id)


# Saved items ---------------------------------------------------------------------------------


@router.get("/saved", response_model=list[SavedItemOut])
def list_saved(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    client = get_supabase_client()
    rows = (
        client.table("saved_items")
        .select(_SAVED_SELECT)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    post_author_ids = {(r.get("posts") or {}).get("author_id") for r in rows if r["kind"] == "post"}
    post_author_ids.discard(None)
    users_by_id, players_by_user_id = _resolve_authors(client, post_author_ids)
    return [
        _saved_item_out(
            r,
            users_by_id.get((r.get("posts") or {}).get("author_id")),
            players_by_user_id.get((r.get("posts") or {}).get("author_id")),
        )
        for r in rows
    ]


@router.post("/saved", response_model=SavedItemOut, status_code=status.HTTP_201_CREATED)
def save_item(payload: SavedItemIn, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()

    if payload.kind == "post":
        if not payload.post_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "postId is required")
        existing = (
            client.table("saved_items")
            .select(_SAVED_SELECT)
            .eq("user_id", user_id)
            .eq("post_id", payload.post_id)
            .maybe_single()
            .execute()
        )
        if existing and existing.data:
            author_id = (existing.data.get("posts") or {}).get("author_id")
            return _saved_item_out(existing.data, *_resolve_author(client, author_id))
        post = client.table("posts").select("id").eq("id", payload.post_id).maybe_single().execute()
        if not post or not post.data:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
        created = client.table("saved_items").insert(
            {"user_id": user_id, "kind": "post", "post_id": payload.post_id}
        ).execute()
    elif payload.kind == "service":
        if not payload.service_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "serviceId is required")
        existing = (
            client.table("saved_items")
            .select(_SAVED_SELECT)
            .eq("user_id", user_id)
            .eq("service_id", payload.service_id)
            .maybe_single()
            .execute()
        )
        if existing and existing.data:
            return _saved_item_out(existing.data)
        service = client.table("services").select("id").eq("id", payload.service_id).maybe_single().execute()
        if not service or not service.data:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
        created = client.table("saved_items").insert(
            {"user_id": user_id, "kind": "service", "service_id": payload.service_id}
        ).execute()
    else:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "kind must be 'post' or 'service'")

    row = client.table("saved_items").select(_SAVED_SELECT).eq("id", created.data[0]["id"]).single().execute().data
    author_id = (row.get("posts") or {}).get("author_id") if row["kind"] == "post" else None
    return _saved_item_out(row, *_resolve_author(client, author_id))


@router.delete("/saved/{saved_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_item(saved_item_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    client = get_supabase_client()
    client.table("saved_items").delete().eq("id", saved_item_id).eq("user_id", user_id).execute()
