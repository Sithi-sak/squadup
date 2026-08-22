import json
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ValidationError

from ..core.auth import get_current_user_id
from ..core.schema import CamelModel
from ..core.storage import upload_file
from ..core.supabase import get_supabase_client

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


class PlayerSummaryOut(CamelModel):
    """`GET /players` list item — the browse-card slice of `PlayerDetailOut`, without the
    services/service_details a card never renders (frontend's `PlayerSummary`)."""

    id: str
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
    handle: str | None
    display_name: str
    avatar_url: str | None
    tagline: str | None
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


class ServiceUpdateIn(CamelModel):
    name: str | None = None
    description: str | None = None
    styles: list[str] | None = None
    platforms: list[str] | None = None
    whats_included: list[str] | None = None
    avg_response_time: str | None = None
    active: bool | None = None


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


def _sorted_pricing(service: dict) -> list[dict]:
    return sorted(service.get("service_pricing_options") or [], key=lambda p: p["sort_order"])


def _service_listing(service: dict) -> dict:
    pricing = _sorted_pricing(service)
    first = pricing[0] if pricing else None
    return {
        "id": service["id"],
        "name": service["name"],
        "promo_badge": _active_promo_label(service.get("service_promotions") or []),
        "price_coins": first["price_coins"] if first else 0,
        "price_unit": first["price_unit"] if first else "/game",
        "active": service["active"],
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
    }


def _service_out(service: dict) -> dict:
    return {**_service_listing(service), **_service_detail(service)}


def _player_summary(player: dict, primary_listing: dict | None) -> dict:
    return {
        "id": player["id"],
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


def _fetch_player_by_id(player_id: str, *, active_only: bool) -> dict:
    result = get_supabase_client().table("players").select("*").eq("id", player_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player not found")
    services = _fetch_services(player_id, active_only=active_only)
    return _serialize_player(result.data, services)


def _fetch_player_by_user_id(user_id: str, *, active_only: bool) -> dict:
    result = (
        get_supabase_client().table("players").select("*").eq("user_id", user_id).maybe_single().execute()
    )
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player profile not found")
    services = _fetch_services(result.data["id"], active_only=active_only)
    return _serialize_player(result.data, services)


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


# Browse -------------------------------------------------------------------------------------
# A distinct path shape from `/{player_id}` (no trailing segment), but kept above the catch-all
# for readability alongside the other literal routes.


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
) -> list[dict]:
    client = get_supabase_client()
    players = client.table("players").select("*").execute().data or []

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

    summaries = [_player_summary(p, services_by_id.get(p.get("highlighted_service_id") or "")) for p in players]

    def matches(player: dict, summary: dict) -> bool:
        if game and not any(g.lower() == game.lower() for g in player["games"]):
            return False
        if rank and (player["rank"] or "").lower() != rank.lower():
            return False
        if role and (player["role"] or "").lower() != role.lower():
            return False
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

    results = [summary for player, summary in zip(players, summaries) if matches(player, summary)]

    if sort == "rating":
        results.sort(key=lambda s: s["rating"] or 0, reverse=True)
    elif sort == "price_asc":
        results.sort(key=lambda s: s["price_coins"] if s["price_coins"] is not None else float("inf"))
    elif sort == "price_desc":
        results.sort(key=lambda s: s["price_coins"] or 0, reverse=True)

    return results


# Own profile ---------------------------------------------------------------------------------
# Registered ahead of the `/{player_id}` catch-all below so `/players/me...` isn't swallowed by it.


@router.get("/me", response_model=PlayerDetailOut)
def get_my_player(user_id: str = Depends(get_current_user_id)) -> dict:
    return _fetch_player_by_user_id(user_id, active_only=False)


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
    avatar_url = upload_file("avatars", f"{user_id}/avatar-{uuid4()}", avatar) if avatar else None
    id_front_url = upload_file("id-documents", f"{user_id}/id-front-{uuid4()}", id_front)
    id_back_url = upload_file("id-documents", f"{user_id}/id-back-{uuid4()}", id_back) if id_back else None

    client.table("players").insert(
        {
            "id": player_id,
            "user_id": user_id,
            "handle": f"@{user_id[:10]}",
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
            "payout_schedule": payout_schedule,
            "id_front_url": id_front_url,
            "id_back_url": id_back_url,
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

    cover_url = upload_file("service-covers", f"{player_id}/cover-{uuid4()}", cover) if cover else None

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
def update_my_service(service_id: str, payload: ServiceUpdateIn, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _get_owned_service(user_id, service_id)

    updates = payload.model_dump(exclude_unset=True)
    if updates:
        client.table("services").update(updates).eq("id", service_id).execute()

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


# Public profile ------------------------------------------------------------------------------
# Catch-all, must stay below every literal `/players/...` route declared above.


@router.get("/{player_id}", response_model=PlayerDetailOut)
def get_player(player_id: str) -> dict:
    return _fetch_player_by_id(player_id, active_only=True)
