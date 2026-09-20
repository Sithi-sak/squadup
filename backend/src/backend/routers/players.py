import json
import random
import re
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ValidationError

from ..core.auth import get_current_user_id, get_optional_user_id
from ..core.blocks import has_blocked
from ..core.schema import CamelModel
from ..core.storage import upload_document, upload_image_as_webp
from ..core.supabase import get_supabase_client
from .feed import _POST_SELECT, PostOut, _serialize_posts

router = APIRouter(prefix="/players", tags=["players"])


# Schemas ---------------------------------------------------------------------------------


class ServiceTypeOption(CamelModel):
    label: str
    price_coins: int
    price_unit: str
    promo_badge: str | None = None


class PlayerServiceListing(CamelModel):
    id: str
    name: str
    promo_badge: str | None
    price_coins: int
    price_unit: str
    active: bool
    cover_image_url: str | None
    # Structured counterpart to `promo_badge`, for prefilling the Edit Service form's promo
    # toggles rather than parsing them back out of the display label.
    first_order_free: bool
    percent_off: float | None


class PlayerServiceDetail(CamelModel):
    title: str
    rating: float | None
    served_count: int
    description: str
    styles: list[str]
    platforms: list[str]
    service_types: list[ServiceTypeOption]
    whats_included: list[str]
    avg_response_time: str
    cover_image_url: str | None


class PlayerSummaryOut(CamelModel):
    """`GET /players` list item — the browse-card slice of `PlayerDetailOut`, without the
    services/service_details a card never renders (frontend's `PlayerSummary`)."""

    id: str
    # Null for a seed Pal with no linked account yet - present so a browse card can follow a
    # Pal (`follows` keys on `users.id`, not `players.id`, see `20260905142123_unify_social_graph`).
    user_id: str | None
    display_name: str
    avatar_url: str | None
    games: list[str]
    rank: str | None
    role: str | None
    price_per_hour: float | None
    languages: list[str]
    rating: float | None
    review_count: int
    tagline: str | None
    price_coins: int | None
    online: bool
    is_new: bool
    promo_badge: str | None


class PlayerDetailOut(CamelModel):
    """Combines what `PlayerSummary` and the core (non-social) slice of `PlayerProfile`
    (frontend/src/stores/players.ts) both need, so `GET /players/{id}` and `GET /players/me`
    can back both the profile header and the services tab from one payload."""

    id: str
    # Never null for `/players/me` (always set on creation), but seed Pals reachable via
    # `/players/{id}` may have no linked account yet.
    user_id: str | None
    handle: str | None
    display_name: str
    avatar_url: str | None
    tagline: str | None
    bio: str | None
    timezone: str | None
    language: str | None
    tier: str | None
    highlight_badge: str | None
    subscribe_label: str | None
    games: list[str]
    rank: str | None
    role: str | None
    languages: list[str]
    price_per_hour: float | None
    rating: float | None
    review_count: int
    online: bool
    is_new: bool
    price_coins: int | None
    promo_badge: str | None
    services: list[PlayerServiceListing]
    highlighted_service_id: str
    service_details: dict[str, PlayerServiceDetail]
    posts_count: int
    followers_count: int
    following_count: int
    # Whether the requesting viewer follows this Pal - always False for `/players/me` (can't
    # follow yourself) and for an anonymous viewer, same as `feed.py`'s per-viewer `following`.
    following: bool
    # True when the viewer is the one who blocked this Pal, so the profile menu offers Unblock.
    # The other direction never reaches here: the Pal's own block makes this read 403 (4.39).
    blocked: bool = False


class RateIn(BaseModel):
    game: str
    price: float | None = None


class ServiceOut(CamelModel):
    id: str
    name: str
    description: str
    styles: list[str]
    platforms: list[str]
    service_types: list[ServiceTypeOption]
    whats_included: list[str]
    avg_response_time: str
    rating: float | None
    served_count: int
    active: bool
    promo_badge: str | None
    price_coins: int
    price_unit: str
    cover_image_url: str | None
    first_order_free: bool
    percent_off: float | None


class PricingOptionIn(BaseModel):
    label: str
    price_coins: int
    price_unit: str


class ServiceCreateForm(BaseModel):
    name: str
    description: str | None = None
    styles: list[str]
    platforms: list[str]
    pricing_options: list[PricingOptionIn]
    first_order_free: bool = False
    percent_off: float | None = None


class EarningsBar(CamelModel):
    label: str
    coins: int


class AlbumItemOut(CamelModel):
    id: str
    kind: str
    label: str | None
    views: int
    likes: int
    shares: int
    duration_seconds: int | None


class WishItemOut(CamelModel):
    id: str
    title: str
    game: str | None
    type: str | None
    price_coins: int
    saved: bool
    service_id: str | None


class EarningsOut(CamelModel):
    """`GET /players/me/earnings` (3.7) — everything derivable from the Pal's own `bookings`
    rows, plus the Pal's own `payout_schedule` and the next run it implies (4.51). Pending
    clearance and payout history come from the wallet endpoints (3.9); nothing on this payload
    is mocked any more."""

    lifetime_earned_coins: int
    lifetime_earned_change_pct: float | None
    coins_this_month: int
    coins_this_month_change_pct: float | None
    orders_completed: int
    orders_completed_this_week: int
    response_rate_pct: int
    earnings_this_week: list[EarningsBar]
    earnings_overview: list[EarningsBar]
    payout_schedule: str
    next_payout_date: str


# Helpers -----------------------------------------------------------------------------------


def _active_promo_label(promotions: list[dict]) -> str | None:
    for promo in promotions:
        if not promo.get("active"):
            continue
        discount_type = promo["discount_type"]
        if discount_type == "first_order_free":
            return "1st Order Free"
        if discount_type == "percent_off" and promo.get("discount_value") is not None:
            return f"{promo['discount_value']:g}% Off"
        if discount_type == "flat_off" and promo.get("discount_value") is not None:
            return f"{promo['discount_value']:g} Off"
    return None


def _active_promo(promotions: list[dict]) -> tuple[bool, float | None]:
    """Structured counterpart to `_active_promo_label`, for prefilling the Edit Service form's
    promo toggles rather than parsing them back out of the display label."""
    for promo in promotions:
        if not promo.get("active"):
            continue
        if promo["discount_type"] == "first_order_free":
            return True, None
        if promo["discount_type"] == "percent_off" and promo.get("discount_value") is not None:
            return False, promo["discount_value"]
    return False, None


def _sorted_pricing(service: dict) -> list[dict]:
    return sorted(service.get("service_pricing_options") or [], key=lambda p: p["sort_order"])


def _service_listing(service: dict) -> dict:
    pricing = _sorted_pricing(service)
    first = pricing[0] if pricing else None
    first_order_free, percent_off = _active_promo(service.get("service_promotions") or [])
    return {
        "id": service["id"],
        "name": service["name"],
        "promo_badge": _active_promo_label(service.get("service_promotions") or []),
        "price_coins": first["price_coins"] if first else 0,
        "price_unit": first["price_unit"] if first else "/game",
        "active": service["active"],
        "cover_image_url": service.get("cover_image_url"),
        "first_order_free": first_order_free,
        "percent_off": percent_off,
    }


def _service_detail(service: dict) -> dict:
    promo = _active_promo_label(service.get("service_promotions") or [])
    return {
        "title": service["name"],
        "rating": service["rating"],
        "served_count": service["served_count"],
        "description": service["description"] or "",
        "styles": service["styles"],
        "platforms": service["platforms"],
        "service_types": [
            {
                "label": option["label"],
                "price_coins": option["price_coins"],
                "price_unit": option["price_unit"],
                "promo_badge": promo,
            }
            for option in _sorted_pricing(service)
        ],
        "whats_included": service["whats_included"],
        "avg_response_time": service["avg_response_time"] or "",
        "cover_image_url": service.get("cover_image_url"),
    }


def _service_out(service: dict) -> dict:
    return {**_service_listing(service), **_service_detail(service)}


def _player_summary(player: dict, primary_listing: dict | None) -> dict:
    return {
        "id": player["id"],
        "user_id": player.get("user_id"),
        "display_name": player["display_name"],
        "avatar_url": player["avatar_url"],
        "games": player["games"],
        "rank": player["rank"],
        "role": player["role"],
        "price_per_hour": player["price_per_hour"],
        "languages": player["languages"],
        "rating": player["rating"],
        "review_count": player["review_count"],
        "tagline": player["tagline"],
        "price_coins": primary_listing["price_coins"] if primary_listing else None,
        "online": player["online"],
        "is_new": player["is_new"],
        "promo_badge": primary_listing["promo_badge"] if primary_listing else None,
    }


def _serialize_player(player: dict, services: list[dict]) -> dict:
    listings = [_service_listing(s) for s in services]
    highlighted = player.get("highlighted_service_id") or (services[0]["id"] if services else "")
    primary = next((listing for listing in listings if listing["id"] == highlighted), None)
    return {
        **player,
        "price_coins": primary["price_coins"] if primary else None,
        "promo_badge": primary["promo_badge"] if primary else None,
        "services": listings,
        "highlighted_service_id": highlighted,
        "service_details": {s["id"]: _service_detail(s) for s in services},
    }


def _fetch_services(player_id: str, *, active_only: bool):
    query = (
        get_supabase_client()
        .table("services")
        .select("*, service_pricing_options(*), service_promotions(*)")
        .eq("player_id", player_id)
    )
    if active_only:
        query = query.eq("active", True)
    return query.execute().data or []


def _with_social_counts(client, player: dict) -> dict:
    """Posts/follows are unified around `users` now (3.18), not `players` - a Pal's own social
    counts live on their `users` row, same place a plain buyer's would. `handle` is unified there
    too (4.14) - a Pal's marketplace handle is just their account username."""
    stub = {"handle": None, "posts_count": 0, "followers_count": 0, "following_count": 0}
    if not player.get("user_id"):
        return {**player, **stub}
    result = (
        client.table("users")
        .select("handle, posts_count, followers_count, following_count")
        .eq("id", player["user_id"])
        .maybe_single()
        .execute()
    )
    counts = result.data if result and result.data else stub
    return {**player, **counts}


def _is_following(client, viewer_id: str | None, target_user_id: str | None) -> bool:
    """Same `follows` lookup `feed.py` batches for the feed list, done for one target here -
    False for an anonymous viewer, a Pal with no linked account, or viewing your own profile."""
    if not viewer_id or not target_user_id or viewer_id == target_user_id:
        return False
    result = (
        client.table("follows")
        .select("follower_id")
        .eq("follower_id", viewer_id)
        .eq("followed_id", target_user_id)
        .maybe_single()
        .execute()
    )
    return bool(result and result.data)


def _fetch_player_by_id(
    player_id: str, *, active_only: bool, public_only: bool = False, viewer_id: str | None = None
) -> dict:
    client = get_supabase_client()
    result = client.table("players").select("*").eq("id", player_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player not found")
    # A pending/rejected application or a banned Pal isn't reachable via the public profile link
    # (3.19), same as it's excluded from `GET /players` - `GET /players/me` passes
    # `public_only=False` so a Pal can always see their own profile regardless of status.
    if public_only and (result.data["status"] != "approved" or result.data["is_banned"]):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player not found")
    # "They can't ... view your profile" (4.39). One-directional: whoever placed the block keeps
    # reading the profile, since that is where Unblock lives.
    owner_user_id = result.data.get("user_id")
    if has_blocked(owner_user_id, viewer_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This profile is unavailable.")
    services = _fetch_services(player_id, active_only=active_only)
    player = _serialize_player(_with_social_counts(client, result.data), services)
    return {
        **player,
        "following": _is_following(client, viewer_id, player.get("user_id")),
        "blocked": has_blocked(viewer_id, owner_user_id),
    }


def _fetch_player_by_user_id(user_id: str, *, active_only: bool) -> dict:
    client = get_supabase_client()
    result = client.table("players").select("*").eq("user_id", user_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player profile not found")
    services = _fetch_services(result.data["id"], active_only=active_only)
    player = _serialize_player(_with_social_counts(client, result.data), services)
    return {**player, "following": False, "blocked": False}


def _require_player_exists(player_id: str) -> None:
    result = get_supabase_client().table("players").select("id").eq("id", player_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player not found")


def _get_owned_service(user_id: str, service_id: str) -> dict:
    result = (
        get_supabase_client()
        .table("services")
        .select("*, players!services_player_id_fkey!inner(user_id)")
        .eq("id", service_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data or result.data["players"]["user_id"] != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
    return result.data


def _pricing_unit(pricing_model: str) -> str:
    return {"per-hour": "/hour", "per-session": "/session"}.get(pricing_model, "/game")


def _match_score(player: dict, *, game: str | None, rank: str | None, role: str | None) -> int:
    """Weighted relevance score used for `GET /players`'s default ordering (3.3): how well a
    Pal matches the browse criteria the caller is searching with. Unlike `q`/`language`/
    `max_price`/`online`/`is_new` below, game/rank/role no longer exclude a partial match (see
    `matches()`), they just rank it lower - a Diamond duo Pal still shows up for a Platinum
    search, just below the exact-rank matches."""
    score = 0
    if game and any(g.lower() == game.lower() for g in player["games"]):
        score += 40
    if rank and (player["rank"] or "").lower() == rank.lower():
        score += 30
    if role and (player["role"] or "").lower() == role.lower():
        score += 20
    if player["online"]:
        score += 10
    return score


# `players.payout_schedule` is a Postgres enum ('weekly' | 'bi_weekly' | 'monthly'). The
# Become-a-Pal wizard and the Settings select both speak the hyphenated "bi-weekly", so every
# write normalizes first - an un-normalized value is rejected by the enum, not coerced.
PAYOUT_SCHEDULES = ("weekly", "bi_weekly", "monthly")


def _normalize_payout_schedule(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_")
    if normalized not in PAYOUT_SCHEDULES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown payout schedule: {value}")
    return normalized


def _next_payout_date(schedule: str, now: datetime) -> str:
    """The next payout run for `schedule`, as a date. There's no payout-run job yet (3.9 pays
    out per approved withdrawal), so this is the calendar answer to "when does my next one
    land": weekly and bi-weekly pay on Mondays (bi-weekly on even ISO weeks), monthly on the
    1st. Kept here rather than on the frontend so the Dashboard and Earnings pages can't drift."""
    if schedule == "monthly":
        year, month = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)
        return datetime(year, month, 1, tzinfo=UTC).date().isoformat()
    # Monday of next week, then for bi-weekly skip to the following one if that lands on an odd
    # ISO week.
    monday = (now + timedelta(days=7 - now.weekday())).date()
    if schedule == "bi_weekly" and monday.isocalendar().week % 2 == 1:
        monday += timedelta(days=7)
    return monday.isoformat()


def _month_key(now: datetime, offset: int) -> tuple[int, int]:
    year, month = now.year, now.month - offset
    while month <= 0:
        month += 12
        year -= 1
    return year, month


def _pct_change(current: int, previous: int) -> float | None:
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def _compute_earnings(bookings: list[dict], payout_schedule: str) -> dict:
    """Aggregates a Pal's own `bookings` rows into `EarningsOut` (3.7), same aggregate-in-Python
    approach as `_match_score`/`list_players` (3.2a/3.3a) rather than composing this in SQL."""
    now = datetime.now(UTC)
    completed = [b for b in bookings if b["status"] == "completed"]

    month_totals: dict[tuple[int, int], int] = defaultdict(int)
    day_totals: dict[str, int] = defaultdict(int)
    for b in completed:
        dt = datetime.fromisoformat(b["created_at"])
        month_totals[(dt.year, dt.month)] += b["total_coins"]
        day_totals[dt.date().isoformat()] += b["total_coins"]

    coins_this_month = month_totals.get(_month_key(now, 0), 0)
    coins_last_month = month_totals.get(_month_key(now, 1), 0)
    change_pct = _pct_change(coins_this_month, coins_last_month)

    week_start = now - timedelta(days=6)
    earnings_this_week = [
        {"label": (now - timedelta(days=i)).strftime("%a")[0], "coins": day_totals.get((now - timedelta(days=i)).date().isoformat(), 0)}
        for i in range(6, -1, -1)
    ]

    earnings_overview = []
    for i in range(7, -1, -1):
        key = _month_key(now, i)
        earnings_overview.append(
            {"label": datetime(key[0], key[1], 1, tzinfo=UTC).strftime("%b"), "coins": month_totals.get(key, 0)}
        )

    orders_completed_this_week = sum(
        1 for b in completed if datetime.fromisoformat(b["created_at"]) >= week_start
    )
    responded = sum(1 for b in bookings if b["status"] != "pending")
    response_rate_pct = round(responded / len(bookings) * 100) if bookings else 100

    return {
        "lifetime_earned_coins": sum(b["total_coins"] for b in completed),
        "lifetime_earned_change_pct": change_pct,
        "coins_this_month": coins_this_month,
        "coins_this_month_change_pct": change_pct,
        "orders_completed": len(completed),
        "orders_completed_this_week": orders_completed_this_week,
        "response_rate_pct": response_rate_pct,
        "earnings_this_week": earnings_this_week,
        "earnings_overview": earnings_overview,
        "payout_schedule": payout_schedule,
        "next_payout_date": _next_payout_date(payout_schedule, now),
    }


# Browse -------------------------------------------------------------------------------------
# A distinct path shape from `/{player_id}` (no trailing segment), but kept above the catch-all
# for readability alongside the other literal routes.


def _player_summaries(client, players: list[dict]) -> list[dict]:
    highlighted_ids = [p["highlighted_service_id"] for p in players if p.get("highlighted_service_id")]
    services_by_id: dict[str, dict] = {}
    if highlighted_ids:
        rows = (
            client.table("services")
            .select("*, service_pricing_options(*), service_promotions(*)")
            .in_("id", highlighted_ids)
            .eq("active", True)
            .execute()
            .data
            or []
        )
        services_by_id = {s["id"]: _service_listing(s) for s in rows}
    return [_player_summary(p, services_by_id.get(p.get("highlighted_service_id") or "")) for p in players]


@router.get("", response_model=list[PlayerSummaryOut])
def list_players(
    q: str | None = None,
    game: str | None = None,
    rank: str | None = None,
    role: str | None = None,
    language: str | None = None,
    max_price: int | None = None,
    online: bool | None = None,
    is_new: bool | None = None,
    sort: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    client = get_supabase_client()

    if limit is not None and not any(
        [q, game, rank, role, language, max_price, online, is_new],
    ):
        # Fast path for callers that only want a small top-rated slice (Home's "eStars"/"More
        # Pals" rails, Landing's "Top Pal") - order/limit in the query itself instead of fetching
        # every approved player just to discard most of them client-side.
        players = (
            client.table("players")
            .select("*")
            .eq("status", "approved")
            .eq("is_banned", False)
            .order("rating", desc=True, nullsfirst=False)
            .limit(limit)
            .execute()
            .data
            or []
        )
        return _player_summaries(client, players)

    players = (
        client.table("players")
        .select("*")
        .eq("status", "approved")
        .eq("is_banned", False)
        .execute()
        .data
        or []
    )

    summaries = _player_summaries(client, players)

    def matches(player: dict, summary: dict) -> bool:
        # game/rank/role are scored (`_match_score`), not filtered here - see that docstring.
        if language and not any(lang.lower() == language.lower() for lang in player["languages"]):
            return False
        if max_price is not None and summary["price_coins"] is not None and summary["price_coins"] > max_price:
            return False
        if online is not None and player["online"] != online:
            return False
        if is_new is not None and player["is_new"] != is_new:
            return False
        if q:
            needle = q.lower()
            haystacks = [player["display_name"], summary["tagline"] or "", *player["games"]]
            if not any(needle in h.lower() for h in haystacks):
                return False
        return True

    results = [
        (summary, _match_score(player, game=game, rank=rank, role=role))
        for player, summary in zip(players, summaries)
        if matches(player, summary)
    ]

    if sort == "rating":
        results.sort(key=lambda item: item[0]["rating"] or 0, reverse=True)
    elif sort == "price_asc":
        results.sort(key=lambda item: item[0]["price_coins"] if item[0]["price_coins"] is not None else float("inf"))
    elif sort == "price_desc":
        results.sort(key=lambda item: item[0]["price_coins"] or 0, reverse=True)
    else:
        # Default order (3.3): highest match score first, stable otherwise.
        results.sort(key=lambda item: item[1], reverse=True)

    return [summary for summary, _score in results]


# Own profile ---------------------------------------------------------------------------------
# Registered ahead of the `/{player_id}` catch-all below so `/players/me...` isn't swallowed by it.


@router.get("/me", response_model=PlayerDetailOut)
def get_my_player(user_id: str = Depends(get_current_user_id)) -> dict:
    return _fetch_player_by_user_id(user_id, active_only=False)


class PlayerProfileUpdateIn(CamelModel):
    """Settings' Profile tab. `display_name` is deliberately absent - it lives on the Account
    tab and `PATCH /users/me` mirrors it onto the player row, so there is one place to rename."""

    tagline: str | None = None
    bio: str | None = None
    languages: list[str] | None = None
    payout_schedule: str | None = None


@router.patch("/me", response_model=PlayerDetailOut)
def update_my_player(
    payload: PlayerProfileUpdateIn,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    client = get_supabase_client()
    player = client.table("players").select("id").eq("user_id", user_id).maybe_single().execute()
    if not player or not player.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player profile not found")
    updates = payload.model_dump(exclude_unset=True)
    if "languages" in updates:
        # `language` is the singular legacy column the About card and browse filters still read;
        # creation keeps it as `languages[0]` and an edit has to follow, or the two disagree.
        updates["language"] = updates["languages"][0] if updates["languages"] else None
    if updates.get("payout_schedule"):
        updates["payout_schedule"] = _normalize_payout_schedule(updates["payout_schedule"])
    if updates:
        client.table("players").update(updates).eq("id", player.data["id"]).execute()
    return _fetch_player_by_user_id(user_id, active_only=False)


@router.patch("/me/avatar", response_model=PlayerDetailOut)
def update_my_player_avatar(
    avatar: UploadFile = File(...),  # noqa: B008
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Settings' Profile tab "Change photo" (4.16) - re-encoded to WebP same as feed/post
    images and the Become-a-Pal wizard's initial avatar."""
    client = get_supabase_client()
    player = client.table("players").select("id").eq("user_id", user_id).maybe_single().execute()
    if not player or not player.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player profile not found")
    avatar_url = upload_image_as_webp("avatars", f"{user_id}/avatar-{uuid4()}", avatar)
    client.table("players").update({"avatar_url": avatar_url}).eq("id", player.data["id"]).execute()
    return _fetch_player_by_user_id(user_id, active_only=False)


@router.get("/me/earnings", response_model=EarningsOut)
def get_my_earnings(user_id: str = Depends(get_current_user_id)) -> dict:
    """Player Dashboard / Earnings (3.7) - not a `_fetch_player_by_user_id` call since only the
    player id is needed here, not the full serialized profile + services."""
    client = get_supabase_client()
    player = (
        client.table("players")
        .select("id, payout_schedule")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not player or not player.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player profile not found")
    bookings = (
        client.table("bookings")
        .select("status, total_coins, created_at")
        .eq("player_id", player.data["id"])
        .execute()
        .data
        or []
    )
    return _compute_earnings(bookings, player.data["payout_schedule"])


@router.post("/me", response_model=PlayerDetailOut, status_code=status.HTTP_201_CREATED)
def create_my_player(
    display_name: str = Form(...),
    tagline: str | None = Form(None),
    timezone: str | None = Form(None),
    games: list[str] = Form(...),  # noqa: B008
    rank: str | None = Form(None),
    role: str | None = Form(None),
    languages: list[str] = Form(...),  # noqa: B008
    payout_schedule: str = Form("weekly"),
    pricing_model: str = Form("per-game"),
    rates: str = Form("[]"),
    offer_first_order_free: bool = Form(False),
    avatar: UploadFile | None = File(None),  # noqa: B008
    id_front: UploadFile = File(...),  # noqa: B008
    id_back: UploadFile | None = File(None),  # noqa: B008
    user_id: str = Depends(get_current_user_id),
) -> dict:
    client = get_supabase_client()

    existing = client.table("players").select("id").eq("user_id", user_id).maybe_single().execute()
    if existing and existing.data:
        raise HTTPException(status.HTTP_409_CONFLICT, "Player profile already exists")

    try:
        parsed_rates = [RateIn.model_validate(r) for r in json.loads(rates)]
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid rates payload") from exc

    player_id = str(uuid4())
    # Every upload here is re-encoded and downscaled first: a raw phone photo is routinely over
    # the `avatars` bucket's 5MB limit, which used to fail the whole submission with a 500.
    avatar_url = upload_image_as_webp("avatars", f"{user_id}/avatar-{uuid4()}", avatar) if avatar else None
    id_front_url = upload_document("id-documents", f"{user_id}/id-front-{uuid4()}", id_front)
    id_back_url = upload_document("id-documents", f"{user_id}/id-back-{uuid4()}", id_back) if id_back else None

    # A Pal's marketplace handle is just their account username (4.14) - only assign the old
    # auto-generated fallback if they haven't already set one in Settings.
    account = client.table("users").select("handle").eq("id", user_id).maybe_single().execute()
    if not (account and account.data and account.data.get("handle")):
        client.table("users").update({"handle": f"@{user_id[:10]}"}).eq("id", user_id).execute()

    client.table("players").insert(
        {
            "id": player_id,
            "user_id": user_id,
            "display_name": display_name,
            "avatar_url": avatar_url,
            "tagline": tagline,
            "timezone": timezone,
            "language": languages[0] if languages else None,
            "tier": "Pal 1",
            "games": games,
            "rank": rank,
            "role": role,
            "languages": languages,
            "payout_schedule": _normalize_payout_schedule(payout_schedule),
            "id_front_url": id_front_url,
            "id_back_url": id_back_url,
            "status": "pending_review",
        }
    ).execute()

    unit = _pricing_unit(pricing_model)
    first_service_id: str | None = None
    for rate in parsed_rates:
        if rate.price is None or rate.price <= 0:
            continue
        service_id = str(uuid4())
        first_service_id = first_service_id or service_id
        client.table("services").insert(
            {"id": service_id, "player_id": player_id, "name": rate.game, "platforms": [rate.game]}
        ).execute()
        client.table("service_pricing_options").insert(
            {
                "service_id": service_id,
                "label": f"Standard {unit.lstrip('/')}",
                "price_coins": int(rate.price),
                "price_unit": unit,
                "sort_order": 0,
            }
        ).execute()
        if offer_first_order_free:
            client.table("service_promotions").insert(
                {"service_id": service_id, "label": "1st Order Free", "discount_type": "first_order_free"}
            ).execute()

    if first_service_id:
        client.table("players").update({"highlighted_service_id": first_service_id}).eq(
            "id", player_id
        ).execute()

    client.table("users").update({"onboarding_complete": True, "display_name": display_name}).eq(
        "id", user_id
    ).execute()

    return _fetch_player_by_user_id(user_id, active_only=False)


# Own services ----------------------------------------------------------------------------


@router.post("/me/services", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
async def create_my_service(
    name: str = Form(...),
    description: str | None = Form(None),
    styles: list[str] = Form(default_factory=list),  # noqa: B008
    platforms: list[str] = Form(default_factory=list),  # noqa: B008
    pricing_options: str = Form(...),
    first_order_free: bool = Form(False),
    percent_off: float | None = Form(None),
    cover: UploadFile | None = File(None),  # noqa: B008
    user_id: str = Depends(get_current_user_id),
) -> dict:
    client = get_supabase_client()

    player = client.table("players").select("id").eq("user_id", user_id).maybe_single().execute()
    if not player or not player.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player profile not found")
    player_id = player.data["id"]

    try:
        parsed_options = [PricingOptionIn.model_validate(o) for o in json.loads(pricing_options)]
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid pricing options") from exc
    if not parsed_options:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "At least one pricing option is required")

    cover_url = upload_image_as_webp("service-covers", f"{player_id}/cover-{uuid4()}", cover) if cover else None

    service_id = str(uuid4())
    client.table("services").insert(
        {
            "id": service_id,
            "player_id": player_id,
            "name": name,
            "description": description,
            "styles": styles,
            "platforms": platforms,
            "cover_image_url": cover_url,
        }
    ).execute()

    for sort_order, option in enumerate(parsed_options):
        client.table("service_pricing_options").insert(
            {
                "service_id": service_id,
                "label": option.label,
                "price_coins": option.price_coins,
                "price_unit": option.price_unit,
                "sort_order": sort_order,
            }
        ).execute()

    if first_order_free:
        client.table("service_promotions").insert(
            {"service_id": service_id, "label": "1st Order Free", "discount_type": "first_order_free"}
        ).execute()
    elif percent_off:
        client.table("service_promotions").insert(
            {
                "service_id": service_id,
                "label": f"{percent_off:g}% Off",
                "discount_type": "percent_off",
                "discount_value": percent_off,
            }
        ).execute()

    result = (
        client.table("services")
        .select("*, service_pricing_options(*), service_promotions(*)")
        .eq("id", service_id)
        .single()
        .execute()
    )
    return _service_out(result.data)


@router.patch("/me/services/{service_id}", response_model=ServiceOut)
async def update_my_service(
    service_id: str,
    name: str | None = Form(None),
    description: str | None = Form(None),
    styles: list[str] | None = Form(None),  # noqa: B008
    platforms: list[str] | None = Form(None),  # noqa: B008
    pricing_options: str | None = Form(None),
    first_order_free: bool | None = Form(None),
    percent_off: float | None = Form(None),
    active: bool | None = Form(None),
    cover: UploadFile | None = File(None),  # noqa: B008
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Partial update - every field is optional and only the ones present in the form are
    touched, so this backs both the lightweight active-toggle (just `active`) and the full
    Edit Service form (everything `create_my_service` accepts, resubmitted wholesale)."""
    client = get_supabase_client()
    service = _get_owned_service(user_id, service_id)

    parsed_options = None
    if pricing_options is not None:
        try:
            parsed_options = [PricingOptionIn.model_validate(o) for o in json.loads(pricing_options)]
        except (json.JSONDecodeError, ValidationError) as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid pricing options") from exc
        if not parsed_options:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "At least one pricing option is required")

    updates: dict = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if styles is not None:
        updates["styles"] = styles
    if platforms is not None:
        updates["platforms"] = platforms
    if active is not None:
        updates["active"] = active
    if cover is not None:
        updates["cover_image_url"] = upload_image_as_webp(
            "service-covers", f"{service['player_id']}/cover-{uuid4()}", cover
        )
    if updates:
        client.table("services").update(updates).eq("id", service_id).execute()

    if parsed_options is not None:
        client.table("service_pricing_options").delete().eq("service_id", service_id).execute()
        for sort_order, option in enumerate(parsed_options):
            client.table("service_pricing_options").insert(
                {
                    "service_id": service_id,
                    "label": option.label,
                    "price_coins": option.price_coins,
                    "price_unit": option.price_unit,
                    "sort_order": sort_order,
                }
            ).execute()

    if first_order_free is not None or percent_off is not None:
        client.table("service_promotions").delete().eq("service_id", service_id).execute()
        if first_order_free:
            client.table("service_promotions").insert(
                {"service_id": service_id, "label": "1st Order Free", "discount_type": "first_order_free"}
            ).execute()
        elif percent_off:
            client.table("service_promotions").insert(
                {
                    "service_id": service_id,
                    "label": f"{percent_off:g}% Off",
                    "discount_type": "percent_off",
                    "discount_value": percent_off,
                }
            ).execute()

    result = (
        client.table("services")
        .select("*, service_pricing_options(*), service_promotions(*)")
        .eq("id", service_id)
        .single()
        .execute()
    )
    return _service_out(result.data)


@router.delete("/me/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_service(service_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    _get_owned_service(user_id, service_id)
    get_supabase_client().table("services").delete().eq("id", service_id).execute()


@router.get("/suggested", response_model=list[PlayerSummaryOut])
def get_suggested_players(user_id: str | None = Depends(get_optional_user_id), limit: int = 4) -> list[dict]:
    """Feed's right-rail "Suggested Pals" - previously mock-only (see CHECKPOINT 3.8a). A random
    sample of approved, account-linked Pals, excluding the viewer themself and anyone already
    followed."""
    client = get_supabase_client()
    players = (
        client.table("players")
        .select("*")
        .eq("status", "approved")
        .eq("is_banned", False)
        .execute()
        .data
        or []
    )
    players = [p for p in players if p.get("user_id")]

    if user_id:
        followed_ids = {
            f["followed_id"]
            for f in client.table("follows").select("followed_id").eq("follower_id", user_id).execute().data or []
        }
        players = [p for p in players if p["user_id"] != user_id and p["user_id"] not in followed_ids]

    random.shuffle(players)
    return _player_summaries(client, players[:limit])


def _slugify(name: str) -> str:
    """Mirrors `frontend/src/data/games.ts`'s `slugify()` exactly, so counts keyed here line up
    with a `FeaturedGame.id` without the frontend needing a second name->id lookup."""
    slug = name.lower()
    slug = re.sub(r"['’]", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return re.sub(r"(^-|-$)", "", slug)


@router.get("/game-counts", response_model=dict[str, int])
def get_game_counts() -> dict[str, int]:
    """Real per-game Pal counts for the "Browse by game" rails (Home/Landing), which previously
    hardcoded fake numbers in `data/games.ts`'s `featuredGames`. Counts every approved,
    non-banned player's `games` entries, keyed by slug so the frontend can look counts up by
    `featuredGame.id` directly."""
    client = get_supabase_client()
    players = (
        client.table("players")
        .select("games")
        .eq("status", "approved")
        .eq("is_banned", False)
        .execute()
        .data
        or []
    )
    counts: dict[str, int] = defaultdict(int)
    for player in players:
        for game in player.get("games") or []:
            counts[_slugify(game)] += 1
    return counts


# Public profile ------------------------------------------------------------------------------
# Catch-all, must stay below every literal `/players/...` route declared above.


@router.get("/{player_id}", response_model=PlayerDetailOut)
def get_player(player_id: str, user_id: str | None = Depends(get_optional_user_id)) -> dict:
    return _fetch_player_by_id(player_id, active_only=True, public_only=True, viewer_id=user_id)


@router.get("/{player_id}/feed", response_model=list[PostOut])
def get_player_feed(player_id: str, user_id: str | None = Depends(get_optional_user_id)) -> list[dict]:
    """Public Feed tab (3.8h) - reuses `feed.py`'s `PostOut`/`_serialize_posts` so a Pal's own
    posts carry the same `liked`/`following` per-viewer fields the main Feed/Following pages do,
    just scoped to this one Pal instead of the global timeline. Posts key off `author_id` (a
    `users.id`) since 3.18, so this looks up the Pal's `user_id` first rather than filtering
    posts by `player_id` directly."""
    client = get_supabase_client()
    player = client.table("players").select("user_id").eq("id", player_id).maybe_single().execute()
    if not player or not player.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player not found")
    author_id = player.data["user_id"]
    if not author_id:
        return []
    rows = (
        client.table("posts")
        .select(_POST_SELECT)
        .eq("author_id", author_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )
    return _serialize_posts(client, rows, user_id)


@router.get("/{player_id}/album", response_model=list[AlbumItemOut])
def get_player_album(player_id: str) -> list[dict]:
    _require_player_exists(player_id)
    return (
        get_supabase_client()
        .table("album_items")
        .select("*")
        .eq("player_id", player_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )


@router.get("/{player_id}/wish", response_model=list[WishItemOut])
def get_player_wish(player_id: str) -> list[dict]:
    """Public Wish tab (3.8b). `wish_items.saved` is a column on the Pal's own row, not a
    per-viewer flag - so it's Pal-authored "still wished for" state, not the buyer-side bookmark
    concept `saved_items` (3.8a) already covers under `kind: 'service'`. The public read filters
    to `saved = true`, mirroring how `_fetch_services` filters the public services list to
    `active = true`; there's no save/unsave mutation here for a viewer to call."""
    _require_player_exists(player_id)
    return (
        get_supabase_client()
        .table("wish_items")
        .select("*")
        .eq("player_id", player_id)
        .eq("saved", True)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )


class PlayerReportIn(CamelModel):
    reason: str
    details: str | None = None


class PlayerReportOut(CamelModel):
    id: str
    status: str
    report_count: int


@router.post("/{player_id}/report", response_model=PlayerReportOut, status_code=status.HTTP_201_CREATED)
def report_player(
    player_id: str,
    payload: PlayerReportIn,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Profile report from `ReportProfileModal.vue`, writing the `admin_flags` row the admin
    moderation queue (`GET /admin/flagged-players`) reads. Reports for the same Pal and reason
    collapse onto one pending row and bump `report_count`, which is what that column was always
    for - the queue should show "3 reports of harassment", not three near-identical cards. A
    reporter who submits the same reason twice doesn't move the count."""
    reason = payload.reason.strip()
    if not reason:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A reason is required")

    client = get_supabase_client()
    player = (
        client.table("players").select("id, user_id").eq("id", player_id).maybe_single().execute()
    )
    if not player or not player.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player not found")
    if player.data.get("user_id") == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't report your own profile")

    details = (payload.details or "").strip() or None

    existing = (
        client.table("admin_flags")
        .select("id, report_count, details, reported_by")
        .eq("player_id", player_id)
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
        # Keep the first reporter's account of what happened, but don't lose a later one just
        # because the first person left the details box empty.
        if details and not row.get("details"):
            update["details"] = details
        client.table("admin_flags").update(update).eq("id", row["id"]).execute()
        return {"id": row["id"], "status": "pending", "report_count": update["report_count"]}

    created = (
        client.table("admin_flags")
        .insert(
            {
                "player_id": player_id,
                "reason": reason,
                "details": details,
                "reported_by": user_id,
                "report_count": 1,
                "status": "pending",
            }
        )
        .execute()
        .data[0]
    )
    return {"id": created["id"], "status": created["status"], "report_count": created["report_count"]}
