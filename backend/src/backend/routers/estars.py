from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter

from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/estars", tags=["estars"])

_PERIOD_WINDOWS = {"week": timedelta(days=7), "month": timedelta(days=30)}


# Schemas ---------------------------------------------------------------------------------


class EstarEntryOut(CamelModel):
    id: str
    rank: int
    display_name: str
    avatar_url: str | None
    category: str | None
    rating: float | None
    coins: int
    trend: str


# Endpoint ----------------------------------------------------------------------------------


@router.get("/leaderboard", response_model=list[EstarEntryOut])
def get_leaderboard(period: str = "week", category: str | None = None) -> list[dict]:
    """Estars Leaderboard (3.12) - ranks players by coins earned from `completed` bookings
    within `period` (`week`/`month`/`all_time`), aggregated in Python over one `bookings` fetch
    plus one batched `services` fetch for the highlighted-service `category` label, same
    aggregate-in-Python approach as `_match_score`/`_compute_earnings` (3.3a/3.7a). No historical
    rank snapshot exists to diff against (same "no data to derive it from" call 3.7d made for
    response time), so `trend` is always `'flat'`."""
    client = get_supabase_client()

    players = client.table("players").select("id, display_name, avatar_url, rating, highlighted_service_id").execute().data or []

    highlighted_ids = [p["highlighted_service_id"] for p in players if p.get("highlighted_service_id")]
    category_by_service_id: dict[str, str] = {}
    if highlighted_ids:
        rows = client.table("services").select("id, name").in_("id", highlighted_ids).execute().data or []
        category_by_service_id = {s["id"]: s["name"] for s in rows}

    bookings_query = client.table("bookings").select("player_id, total_coins, created_at").eq("status", "completed")
    window = _PERIOD_WINDOWS.get(period)
    if window is not None:
        cutoff = (datetime.now(UTC) - window).isoformat()
        bookings_query = bookings_query.gte("created_at", cutoff)
    bookings = bookings_query.execute().data or []

    coins_by_player: dict[str, int] = defaultdict(int)
    for booking in bookings:
        coins_by_player[booking["player_id"]] += booking["total_coins"]

    entries = []
    for player in players:
        coins = coins_by_player.get(player["id"], 0)
        if coins <= 0:
            continue
        player_category = category_by_service_id.get(player.get("highlighted_service_id") or "")
        if category and (player_category or "").lower() != category.lower():
            continue
        entries.append(
            {
                "id": player["id"],
                "display_name": player["display_name"],
                "avatar_url": player["avatar_url"],
                "category": player_category,
                "rating": player["rating"],
                "coins": coins,
                "trend": "flat",
            }
        )

    entries.sort(key=lambda entry: entry["coins"], reverse=True)
    for rank, entry in enumerate(entries, start=1):
        entry["rank"] = rank

    return entries
