import logging

from fastapi import APIRouter, Depends, HTTPException, status
from postgrest.exceptions import APIError

from ..core.auth import get_current_user_id, get_optional_user_id
from ..core.blocks import has_blocked
from ..core.schema import CamelModel
from ..core.storage import remove_prefix
from ..core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


class UserOut(CamelModel):
    id: str
    email: str
    display_name: str | None
    handle: str | None
    phone: str | None
    country: str | None
    role: str
    onboarding_complete: bool
    coin_balance: int


class PublicProfileOut(CamelModel):
    id: str
    display_name: str | None
    handle: str | None
    avatar_url: str | None
    online: bool
    # Non-null only when this account has also become a Pal - feed posts and public profile
    # links branch on this to route to the full `/players/{id}` page instead of a plain profile.
    player_id: str | None
    tier: str | None
    posts_count: int
    followers_count: int
    following_count: int
    following: bool
    # True when the viewer is the one who blocked this account, so the profile menu can offer
    # Unblock. The reverse case (they blocked the viewer) never reaches here - the read 403s.
    blocked: bool = False


class UserUpdateIn(CamelModel):
    display_name: str | None = None
    handle: str | None = None
    phone: str | None = None
    country: str | None = None


def _fetch_user(user_id: str) -> dict:
    result = get_supabase_client().table("users").select("*").eq("id", user_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return result.data


@router.get("/me", response_model=UserOut)
def get_me(user_id: str = Depends(get_current_user_id)) -> dict:
    return _fetch_user(user_id)


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdateIn, user_id: str = Depends(get_current_user_id)) -> dict:
    updates = payload.model_dump(exclude_unset=True)
    # Handles are always stored with a leading "@" (players.py's auto-generated Pal handles and
    # every seeded mock follow this too) so every UI that renders `handle` raw stays consistent.
    if updates.get("handle"):
        updates["handle"] = "@" + updates["handle"].lstrip("@")
    if updates:
        client = get_supabase_client()
        try:
            client.table("users").update(updates).eq("id", user_id).execute()
        except APIError as exc:
            if exc.code == "23505":
                raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken") from exc
            raise
        # `players` keeps its own `display_name` copy (marketplace cards, search, the Pal profile
        # header all read it straight off the player row), so a rename from Settings has to reach
        # it too or the Pal page keeps showing the old name. `handle` needs no such mirror - it
        # was unified onto `users` in 4.14.
        if "display_name" in updates:
            client.table("players").update({"display_name": updates["display_name"]}).eq(
                "user_id", user_id
            ).execute()
    return _fetch_user(user_id)


# Every bucket this account could own objects in, with the id its upload paths are keyed by
# (4.52). `service-covers` is the odd one out: covers are written under the *player* id, since a
# service belongs to the Pal profile rather than the account.
_OWNED_BUCKETS = ("avatars", "post-images", "message-images", "id-documents")
_PLAYER_OWNED_BUCKETS = ("service-covers",)


def _delete_stored_files(user_id: str, player_id: str | None) -> None:
    """Sweeps this account's uploads out of Storage. Nothing here can abort the deletion: a bucket
    that errors is logged and skipped, because leaving someone unable to delete their account over
    a stray file is the worse failure. Only `{owner_id}/` prefixes are touched, so no other
    account's files are reachable from here."""
    targets = [(bucket, user_id) for bucket in _OWNED_BUCKETS]
    if player_id:
        targets += [(bucket, player_id) for bucket in _PLAYER_OWNED_BUCKETS]
    for bucket, prefix in targets:
        try:
            remove_prefix(bucket, prefix)
        except Exception:  # best effort - the account deletion below still runs
            logger.exception("Could not clear %s/%s during account deletion", bucket, prefix)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user_id: str = Depends(get_current_user_id)) -> None:
    # `auth.users` -> `public.users` -> `players` -> everything else cascades in one transaction
    # per the 3.13c migration, so no explicit row cleanup is needed here. Storage is a different
    # story: the cascade never reaches `storage.objects`, so uploads (including the private
    # `id-documents` KYC scans, and public URLs that would otherwise keep serving forever) are
    # swept first, while the rows that name them still exist (4.52).
    client = get_supabase_client()
    player = client.table("players").select("id").eq("user_id", user_id).maybe_single().execute()
    _delete_stored_files(user_id, player.data["id"] if player and player.data else None)
    client.auth.admin.delete_user(user_id)


@router.get("/{user_id}/profile", response_model=PublicProfileOut)
def get_public_profile(user_id: str, viewer_id: str | None = Depends(get_optional_user_id)) -> dict:
    """Backs the Feed's "click a name" navigation (clickable post authors) and the plain-buyer
    profile page it lands non-Pals on - a Pal author routes to `/players/{playerId}` instead,
    using this same `playerId`/`tier` pair to decide which."""
    client = get_supabase_client()
    # "They can't ... view your profile" (4.39). One-directional on purpose: the person who
    # blocked still reads the profile, since that is where Unblock lives.
    if has_blocked(user_id, viewer_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This profile is unavailable.")
    user = (
        client.table("users")
        .select("id, display_name, handle, posts_count, followers_count, following_count")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if not user or not user.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    player = (
        client.table("players")
        .select("id, tier, avatar_url, online")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    player_data = player.data if player and player.data else {}

    following = False
    if viewer_id and viewer_id != user_id:
        follow = (
            client.table("follows")
            .select("follower_id")
            .eq("follower_id", viewer_id)
            .eq("followed_id", user_id)
            .maybe_single()
            .execute()
        )
        following = bool(follow and follow.data)

    return {
        "id": user.data["id"],
        "display_name": user.data.get("display_name"),
        "handle": user.data.get("handle"),
        "avatar_url": player_data.get("avatar_url"),
        "online": bool(player_data.get("online")),
        "player_id": player_data.get("id"),
        "tier": player_data.get("tier"),
        "posts_count": user.data.get("posts_count") or 0,
        "followers_count": user.data.get("followers_count") or 0,
        "following_count": user.data.get("following_count") or 0,
        "following": following,
        "blocked": has_blocked(viewer_id, user_id),
    }


# Blocks ------------------------------------------------------------------------------------
# A block stops messaging and booking in both directions, hides each side's posts from the
# other's feed, and makes the blocker's profile unreadable to the person they blocked. Only the
# blocker can lift it (`DELETE`), which is why the row is stored one-directional.


def _resync_follow_counts(client, user_ids: list[str]) -> None:
    """Both sides' `followers_count`/`following_count` after a block dropped their follows -
    recomputed from `follows` the same way `feed.py`'s `_refresh_follow` does, rather than
    decrementing and hoping the stored counts were right."""
    for uid in user_ids:
        followers = len(client.table("follows").select("follower_id").eq("followed_id", uid).execute().data or [])
        following = len(client.table("follows").select("followed_id").eq("follower_id", uid).execute().data or [])
        client.table("users").update({"followers_count": followers, "following_count": following}).eq(
            "id", uid
        ).execute()


class BlockedUserOut(CamelModel):
    id: str
    display_name: str | None
    handle: str | None
    avatar_url: str | None
    blocked_at: str


class BlockStatusOut(CamelModel):
    blocked: bool


@router.get("/me/blocks", response_model=list[BlockedUserOut])
def list_my_blocks(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    client = get_supabase_client()
    rows = (
        client.table("user_blocks")
        .select("blocked_id, created_at, users!user_blocks_blocked_id_fkey(display_name, handle)")
        .eq("blocker_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    if not rows:
        return []

    blocked_ids = [row["blocked_id"] for row in rows]
    players = (
        client.table("players").select("user_id, avatar_url").in_("user_id", blocked_ids).execute().data or []
    )
    avatars = {p["user_id"]: p.get("avatar_url") for p in players}

    return [
        {
            "id": row["blocked_id"],
            "display_name": (row.get("users") or {}).get("display_name"),
            "handle": (row.get("users") or {}).get("handle"),
            "avatar_url": avatars.get(row["blocked_id"]),
            "blocked_at": row["created_at"],
        }
        for row in rows
    ]


@router.post("/blocks/{target_id}", response_model=BlockStatusOut, status_code=status.HTTP_201_CREATED)
def block_user(target_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    if target_id == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't block yourself")
    client = get_supabase_client()
    _fetch_user(target_id)

    client.table("user_blocks").upsert(
        {"blocker_id": user_id, "blocked_id": target_id},
        on_conflict="blocker_id,blocked_id",
    ).execute()

    # Blocking someone you follow (or who follows you) and leaving the follow in place would put
    # their posts back in your Following feed, so both directions go.
    client.table("follows").delete().eq("follower_id", user_id).eq("followed_id", target_id).execute()
    client.table("follows").delete().eq("follower_id", target_id).eq("followed_id", user_id).execute()
    _resync_follow_counts(client, [user_id, target_id])
    return {"blocked": True}


@router.delete("/blocks/{target_id}", response_model=BlockStatusOut)
def unblock_user(target_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    """Unblocking only removes the row - the follows dropped when the block was created are not
    restored, same as everywhere else that treats a block as a clean break."""
    get_supabase_client().table("user_blocks").delete().eq("blocker_id", user_id).eq(
        "blocked_id", target_id
    ).execute()
    return {"blocked": False}
