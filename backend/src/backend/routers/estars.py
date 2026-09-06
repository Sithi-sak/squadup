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
    within `period` (`week`/`month`/`all_time`). The join/sum/filter (previously done in Python
    over a full `players` + `bookings` fetch - 3 sequential REST round-trips, unbounded for
    `all_time`) now happens in Postgres via the `estars_leaderboard` RPC (see its migration),
    returning just the already-aggregated rows in one round-trip. No historical rank snapshot
    exists to diff against (same "no data to derive it from" call 3.7d made for response time),
    so `trend` is always `'flat'`."""
    client = get_supabase_client()

    window = _PERIOD_WINDOWS.get(period)
    cutoff = (datetime.now(UTC) - window).isoformat() if window is not None else None

    rows = (
        client.rpc("estars_leaderboard", {"cutoff": cutoff, "category_filter": category})
        .execute()
        .data
        or []
    )

    entries = []
    for rank, row in enumerate(rows, start=1):
        entries.append(
            {
                "id": row["id"],
                "rank": rank,
                "display_name": row["display_name"],
                "avatar_url": row["avatar_url"],
                "category": row["category"],
                "rating": row["rating"],
                "coins": row["coins"],
                "trend": "flat",
            }
        )

    return entries
