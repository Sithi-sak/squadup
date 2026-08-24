from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field

from ..core.auth import get_current_user_id, get_optional_user_id
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/feed", tags=["feed"])


# Schemas ---------------------------------------------------------------------------------


class PostCreateIn(CamelModel):
    text: str | None = None
    image_url: str | None = None
    category: str = "games"


class PostOut(CamelModel):
    id: str
    player_id: str
    author: str
    handle: str | None
    tier: str | None
    avatar_url: str | None
    online: bool
    text: str | None
    has_image: bool
    category: str
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
    parent_comment_id: str | None
    text: str
    likes: int
    liked: bool
    is_creator: bool
    created_at: str
    replies: list["CommentOut"] = Field(default_factory=list)


class FollowOut(CamelModel):
    player_id: str
    following: bool
    followers_count: int


class SavedItemIn(CamelModel):
    kind: str
    post_id: str | None = None
    service_id: str | None = None


class SavedItemOut(CamelModel):
    id: str
    kind: str
    created_at: str
    post_id: str | None = None
    author: str | None = None
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


# Helpers -----------------------------------------------------------------------------------

_POST_SELECT = "*, players(user_id, display_name, handle, tier, avatar_url, online)"
_COMMENT_SELECT = "*, users!comments_author_id_fkey(display_name)"
_SAVED_SELECT = (
    "*, posts(*, players!posts_player_id_fkey(display_name, handle, tier)), "
    "services(*, players!services_player_id_fkey(display_name), service_pricing_options(*), service_promotions(*))"
)


def _get_post(client, post_id: str) -> dict:
    result = client.table("posts").select(_POST_SELECT).eq("id", post_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return result.data


def _get_player_row(client, player_id: str) -> dict:
    result = client.table("players").select("id, user_id").eq("id", player_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player not found")
    return result.data


def _get_my_player_id(client, user_id: str) -> str:
    result = client.table("players").select("id").eq("user_id", user_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player profile not found")
    return result.data["id"]


def _is_following(client, player_id: str, user_id: str | None) -> bool:
    if not user_id:
        return False
    result = (
        client.table("follows")
        .select("player_id")
        .eq("follower_id", user_id)
        .eq("player_id", player_id)
        .maybe_single()
        .execute()
    )
    return bool(result and result.data)


def _post_out(row: dict, *, liked: bool, following: bool) -> dict:
    player = row.get("players") or {}
    return {
        "id": row["id"],
        "player_id": row["player_id"],
        "author": player.get("display_name") or "SquadUp Pal",
        "handle": player.get("handle"),
        "tier": player.get("tier"),
        "avatar_url": player.get("avatar_url"),
        "online": bool(player.get("online")),
        "text": row["text"],
        "has_image": row["image_url"] is not None,
        "category": row["category"],
        "likes": row["likes_count"],
        "comments": row["comments_count"],
        "liked": liked,
        "following": following,
        "created_at": row["created_at"],
    }


def _serialize_posts(client, rows: list[dict], viewer_id: str | None) -> list[dict]:
    if not rows:
        return []
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
        player_ids = list({r["player_id"] for r in rows})
        following_ids = {
            f["player_id"]
            for f in client.table("follows")
            .select("player_id")
            .eq("follower_id", viewer_id)
            .in_("player_id", player_ids)
            .execute()
            .data
            or []
        }
    return [_post_out(r, liked=r["id"] in liked_ids, following=r["player_id"] in following_ids) for r in rows]


def _refresh_post(client, post_id: str, viewer_id: str, *, liked: bool) -> dict:
    count = len(client.table("post_likes").select("user_id").eq("post_id", post_id).execute().data or [])
    client.table("posts").update({"likes_count": count}).eq("id", post_id).execute()
    row = _get_post(client, post_id)
    return _post_out(row, liked=liked, following=_is_following(client, row["player_id"], viewer_id))


def _refresh_posts_count(client, player_id: str) -> None:
    count = len(client.table("posts").select("id").eq("player_id", player_id).execute().data or [])
    client.table("players").update({"posts_count": count}).eq("id", player_id).execute()


def _refresh_comments_count(client, post_id: str) -> None:
    count = len(client.table("comments").select("id").eq("post_id", post_id).execute().data or [])
    client.table("posts").update({"comments_count": count}).eq("id", post_id).execute()


def _comment_out(row: dict, *, liked: bool, creator_user_id: str | None) -> dict:
    author = (row.get("users") or {}).get("display_name") or "SquadUp user"
    return {
        "id": row["id"],
        "post_id": row["post_id"],
        "author_id": row["author_id"],
        "author": author,
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
        .select(f"{_COMMENT_SELECT}, posts(players(user_id))")
        .eq("id", comment_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    row = result.data
    creator_user_id = ((row.get("posts") or {}).get("players") or {}).get("user_id")
    return row, creator_user_id


def _refresh_comment(client, comment_id: str, *, liked: bool) -> dict:
    count = len(client.table("comment_likes").select("user_id").eq("comment_id", comment_id).execute().data or [])
    client.table("comments").update({"likes_count": count}).eq("id", comment_id).execute()
    row, creator_user_id = _get_comment_with_creator(client, comment_id)
    return _comment_out(row, liked=liked, creator_user_id=creator_user_id)


def _refresh_follow(client, player_id: str, follower_id: str, *, following: bool) -> dict:
    followers_count = len(client.table("follows").select("follower_id").eq("player_id", player_id).execute().data or [])
    client.table("players").update({"followers_count": followers_count}).eq("id", player_id).execute()

    follower_player = client.table("players").select("id").eq("user_id", follower_id).maybe_single().execute()
    if follower_player and follower_player.data:
        following_count = len(
            client.table("follows").select("player_id").eq("follower_id", follower_id).execute().data or []
        )
        client.table("players").update({"following_count": following_count}).eq(
            "id", follower_player.data["id"]
        ).execute()

    return {"player_id": player_id, "following": following, "followers_count": followers_count}


def _service_promo_label(service: dict) -> str | None:
    for promo in service.get("service_promotions") or []:
        if promo.get("active"):
            return promo.get("label")
    return None


def _saved_item_out(row: dict) -> dict:
    base = {"id": row["id"], "kind": row["kind"], "created_at": row["created_at"]}
    if row["kind"] == "post":
        post = row.get("posts") or {}
        player = post.get("players") or {}
        return {
            **base,
            "post_id": row["post_id"],
            "author": player.get("display_name"),
            "handle": player.get("handle"),
            "tier": player.get("tier"),
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
def list_feed(user_id: str | None = Depends(get_optional_user_id)) -> list[dict]:
    client = get_supabase_client()
    rows = (
        client.table("posts").select(_POST_SELECT).order("created_at", desc=True).limit(50).execute().data or []
    )
    return _serialize_posts(client, rows, user_id)


@router.get("/following", response_model=list[PostOut])
def list_following_feed(user_id: str | None = Depends(get_optional_user_id)) -> list[dict]:
    if not user_id:
        return []
    client = get_supabase_client()
    followed = client.table("follows").select("player_id").eq("follower_id", user_id).execute().data or []
    player_ids = [f["player_id"] for f in followed]
    if not player_ids:
        return []
    rows = (
        client.table("posts")
        .select(_POST_SELECT)
        .in_("player_id", player_ids)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )
    return _serialize_posts(client, rows, user_id)


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreateIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """The Feed composer (`CreatePostModal.vue`) - only a Pal has a `players` row to post from,
    same "requires a player profile" convention as `create_my_service`/`get_my_earnings`."""
    client = get_supabase_client()
    player_id = _get_my_player_id(client, user_id)

    text = (payload.text or "").strip() or None
    if not text and not payload.image_url:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Post must have text or an image")

    post_id = str(uuid4())
    client.table("posts").insert(
        {
            "id": post_id,
            "player_id": player_id,
            "text": text,
            "image_url": payload.image_url,
            "category": payload.category,
        }
    ).execute()
    _refresh_posts_count(client, player_id)

    row = _get_post(client, post_id)
    return _post_out(row, liked=False, following=False)


@router.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: str, user_id: str | None = Depends(get_optional_user_id)) -> dict:
    client = get_supabase_client()
    row = _get_post(client, post_id)
    return _serialize_posts(client, [row], user_id)[0]


@router.post("/posts/{post_id}/like", response_model=PostOut)
def like_post(post_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _get_post(client, post_id)
    client.table("post_likes").upsert({"user_id": user_id, "post_id": post_id}).execute()
    return _refresh_post(client, post_id, user_id, liked=True)


@router.delete("/posts/{post_id}/like", response_model=PostOut)
def unlike_post(post_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _get_post(client, post_id)
    client.table("post_likes").delete().eq("user_id", user_id).eq("post_id", post_id).execute()
    return _refresh_post(client, post_id, user_id, liked=False)


# Comments --------------------------------------------------------------------------------


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: str, user_id: str | None = Depends(get_optional_user_id)) -> list[dict]:
    client = get_supabase_client()
    post = _get_post(client, post_id)
    creator_user_id = (post.get("players") or {}).get("user_id")

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

    out_rows = [_comment_out(r, liked=r["id"] in liked_ids, creator_user_id=creator_user_id) for r in rows]
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
    creator_user_id = (post.get("players") or {}).get("user_id")
    return _comment_out(row, liked=False, creator_user_id=creator_user_id)


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


@router.post("/follows/{player_id}", response_model=FollowOut)
def follow_player(player_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    player = _get_player_row(client, player_id)
    if player["user_id"] == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot follow yourself")
    client.table("follows").upsert({"follower_id": user_id, "player_id": player_id}).execute()
    return _refresh_follow(client, player_id, user_id, following=True)


@router.delete("/follows/{player_id}", response_model=FollowOut)
def unfollow_player(player_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _get_player_row(client, player_id)
    client.table("follows").delete().eq("follower_id", user_id).eq("player_id", player_id).execute()
    return _refresh_follow(client, player_id, user_id, following=False)


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
    return [_saved_item_out(r) for r in rows]


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
            return _saved_item_out(existing.data)
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
    return _saved_item_out(row)


@router.delete("/saved/{saved_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_item(saved_item_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    client = get_supabase_client()
    client.table("saved_items").delete().eq("id", saved_item_id).eq("user_id", user_id).execute()
