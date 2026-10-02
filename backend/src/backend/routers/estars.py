from datetime import UTC, datetime, timedelta

from fastapi import APIRouter

from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/estars", tags=["estars"])

_PERIOD_WINDOWS = {"week": timedelta(days=7), "month": timedelta(days=30)}

# `all_time` has no window to step back by, so its trend compares against the standings as of
# this long ago instead.
_ALL_TIME_TREND_LOOKBACK = timedelta(days=7)


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
    rank_change: int | None


# Endpoint ----------------------------------------------------------------------------------


def _ranking(
    client, cutoff: datetime | None, until: datetime | None, category: str | None
) -> list[dict]:
    params = {
        "cutoff": cutoff.isoformat() if cutoff else None,
        "category_filter": category,
        "until": until.isoformat() if until else None,
    }
    return client.rpc("estars_leaderboard", params).execute().data or []


@router.get("/leaderboard", response_model=list[EstarEntryOut])
def get_leaderboard(period: str = "week", category: str | None = None) -> list[dict]:
    """Estars Leaderboard (3.12) - ranks players by coins earned from `completed` bookings
    within `period` (`week`/`month`/`all_time`). The join/sum/filter happens in Postgres via the
    `estars_leaderboard` RPC (see its migrations), returning just the already-aggregated rows.

    `trend` (4.60) compares each player's rank with their rank in the previous period, ranked
    the same way from `bookings` (no snapshot table needed): `week`/`month` step back one window
    (the 7/30 days before this one), `all_time` compares with the standings as of
    `_ALL_TIME_TREND_LOOKBACK` ago. `rank_change` is places moved (positive = climbed), `None`
    when the player wasn't ranked last period (a new entry, `trend` `'up'`)."""
    client = get_supabase_client()
    now = datetime.now(UTC)

    window = _PERIOD_WINDOWS.get(period)
    if window is not None:
        cutoff, prev_cutoff, prev_until = now - window, now - 2 * window, now - window
    else:
        cutoff, prev_cutoff, prev_until = None, None, now - _ALL_TIME_TREND_LOOKBACK

    rows = _ranking(client, cutoff, None, category)
    prev_rows = _ranking(client, prev_cutoff, prev_until, category)
    prev_ranks = {row["id"]: rank for rank, row in enumerate(prev_rows, start=1)}

    entries = []
    for rank, row in enumerate(rows, start=1):
        prev_rank = prev_ranks.get(row["id"])
        rank_change = None if prev_rank is None else prev_rank - rank
        if rank_change is None or rank_change > 0:
            trend = "up"
        elif rank_change < 0:
            trend = "down"
        else:
            trend = "flat"
        entries.append(
            {
                "id": row["id"],
                "rank": rank,
                "display_name": row["display_name"],
                "avatar_url": row["avatar_url"],
                "category": row["category"],
                "rating": row["rating"],
                "coins": row["coins"],
                "trend": trend,
                "rank_change": rank_change,
            }
        )

    return entries
