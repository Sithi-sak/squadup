from fastapi import APIRouter, Depends, HTTPException, status
from postgrest.exceptions import APIError

from ..core.auth import get_current_user_id, get_optional_user_id
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

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
        try:
            get_supabase_client().table("users").update(updates).eq("id", user_id).execute()
        except APIError as exc:
            if exc.code == "23505":
                raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken") from exc
            raise
    return _fetch_user(user_id)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user_id: str = Depends(get_current_user_id)) -> None:
    # `auth.users` -> `public.users` -> `players` -> everything else cascades in one transaction
    # per the 3.13c migration, so no explicit pre-cleanup is needed here.
    get_supabase_client().auth.admin.delete_user(user_id)


@router.get("/{user_id}/profile", response_model=PublicProfileOut)
def get_public_profile(user_id: str, viewer_id: str | None = Depends(get_optional_user_id)) -> dict:
    """Backs the Feed's "click a name" navigation (clickable post authors) and the plain-buyer
    profile page it lands non-Pals on - a Pal author routes to `/players/{playerId}` instead,
    using this same `playerId`/`tier` pair to decide which."""
    client = get_supabase_client()
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
    }
