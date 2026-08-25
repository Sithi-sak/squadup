from datetime import UTC, datetime

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


class AdminDisputeOut(CamelModel):
    id: str
    order_number: str
    buyer_name: str
    pal_name: str
    service_label: str
    reason: str
    total_coins: int
    opened_at: str
    status: str


class AdminDisputeStatusIn(CamelModel):
    status: str


# Helpers -----------------------------------------------------------------------------------

_FLAG_SELECT = "*, players(display_name, avatar_url), users(display_name)"

_DISPUTE_SELECT = (
    "*, bookings(order_number, total_coins, quantity, service_type_label, "
    "players(display_name), users(display_name))"
)


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


def _dispute_out(row: dict) -> dict:
    booking = row.get("bookings") or {}
    pal = booking.get("players") or {}
    buyer = booking.get("users") or {}
    quantity = booking.get("quantity") or 1
    service_type_label = booking.get("service_type_label") or "Service"
    return {
        **row,
        "order_number": booking.get("order_number") or "-",
        "buyer_name": buyer.get("display_name") or "A buyer",
        "pal_name": pal.get("display_name") or "A Pal",
        # No single field captures a human unit ("games"/"hours"/...) across every service
        # type, so quantity is expressed generically rather than guessing one from `price_unit`.
        "service_label": f"{service_type_label} · {quantity} session{'' if quantity == 1 else 's'}",
        "total_coins": booking.get("total_coins") or 0,
        "opened_at": row["created_at"],
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


# Disputes -------------------------------------------------------------------------------
# Same no-auth posture as flagged players above.


@router.get("/disputes", response_model=list[AdminDisputeOut])
def list_disputes() -> list[dict]:
    rows = (
        get_supabase_client()
        .table("order_disputes")
        .select(_DISPUTE_SELECT)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return [_dispute_out(row) for row in rows]


@router.patch("/disputes/{dispute_id}/status", response_model=AdminDisputeOut)
def update_dispute_status(dispute_id: str, payload: AdminDisputeStatusIn) -> dict:
    client = get_supabase_client()
    existing = (
        client.table("order_disputes").select("id").eq("id", dispute_id).maybe_single().execute()
    )
    if not existing or not existing.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dispute not found")

    update: dict = {"status": payload.status}
    if payload.status in ("resolved", "refunded"):
        update["resolved_at"] = datetime.now(UTC).isoformat()
    client.table("order_disputes").update(update).eq("id", dispute_id).execute()
    result = (
        client.table("order_disputes")
        .select(_DISPUTE_SELECT)
        .eq("id", dispute_id)
        .single()
        .execute()
    )
    return _dispute_out(result.data)
