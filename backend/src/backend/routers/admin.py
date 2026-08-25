from fastapi import APIRouter, HTTPException, status

from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/admin", tags=["admin"])


# Schemas ---------------------------------------------------------------------------------


class AdminFlaggedPlayerOut(CamelModel):
    id: str
    player_id: str
    display_name: str
    avatar_url: str | None
    reason: str
    details: str | None
    reported_by: str
    report_count: int
    reported_at: str
    status: str


class AdminFlagStatusIn(CamelModel):
    status: str


# Helpers -----------------------------------------------------------------------------------

_FLAG_SELECT = "*, players(display_name, avatar_url), users(display_name)"


def _flag_out(row: dict) -> dict:
    player = row.get("players") or {}
    reporter = row.get("users") or {}
    return {
        **row,
        "display_name": player.get("display_name") or "Unknown Pal",
        "avatar_url": player.get("avatar_url"),
        "reported_by": reporter.get("display_name") or "A user",
        "reported_at": row["created_at"],
    }


# Flagged players ------------------------------------------------------------------------
# No auth dependency: `stores/admin.ts`'s mock-credential gate (`admin@squadup.gg`,
# session-only) is the only guard until real admin auth ships (per the 1.15 checkpoint note).


@router.get("/flagged-players", response_model=list[AdminFlaggedPlayerOut])
def list_flagged_players() -> list[dict]:
    rows = (
        get_supabase_client()
        .table("admin_flags")
        .select(_FLAG_SELECT)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return [_flag_out(row) for row in rows]


@router.patch("/flagged-players/{flag_id}/status", response_model=AdminFlaggedPlayerOut)
def update_flagged_player_status(flag_id: str, payload: AdminFlagStatusIn) -> dict:
    client = get_supabase_client()
    existing = client.table("admin_flags").select("id").eq("id", flag_id).maybe_single().execute()
    if not existing or not existing.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Flag not found")

    client.table("admin_flags").update({"status": payload.status}).eq("id", flag_id).execute()
    result = client.table("admin_flags").select(_FLAG_SELECT).eq("id", flag_id).single().execute()
    return _flag_out(result.data)
