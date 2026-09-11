from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, HTTPException, status

from ..core.schema import CamelModel
from ..core.storage import create_signed_url
from ..core.supabase import get_supabase_client
from ..core.wallet import adjust_coin_balance

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
    is_banned: bool


class AdminBanIn(CamelModel):
    is_banned: bool


class AdminPalApplicationOut(CamelModel):
    id: str
    display_name: str
    avatar_url: str | None
    email: str
    tagline: str | None
    timezone: str | None
    games: list[str]
    rank: str | None
    role: str | None
    languages: list[str]
    payout_schedule: str
    id_front_url: str | None
    id_back_url: str | None
    submitted_at: str
    status: str


class AdminPalApplicationStatusIn(CamelModel):
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


class AdminReportDayOut(CamelModel):
    day: str
    count: int


class AdminOverviewOut(CamelModel):
    total_users: int
    total_pals: int
    orders_today: int
    coins_in_escrow: int
    total_commission_coins: int
    reports_this_week: list[AdminReportDayOut]


# Helpers -----------------------------------------------------------------------------------

_ESCROW_STATUSES = ("pending", "accepted")
_WEEKDAY_LABELS = ("M", "T", "W", "T", "F", "S", "S")

_FLAG_SELECT = "*, players(display_name, avatar_url, is_banned), users(display_name)"

_PAL_APPLICATION_SELECT = "*, users(email)"

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
        "is_banned": bool(player.get("is_banned")),
    }


def _pal_application_out(row: dict) -> dict:
    user = row.get("users") or {}
    return {
        **row,
        "email": user.get("email") or "",
        "id_front_url": create_signed_url("id-documents", row["id_front_url"]) if row.get("id_front_url") else None,
        "id_back_url": create_signed_url("id-documents", row["id_back_url"]) if row.get("id_back_url") else None,
        "submitted_at": row["created_at"],
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


# Pal applications ------------------------------------------------------------------------
# Same no-auth posture as the rest of this router - see the note on the Flagged players
# section below.


@router.get("/pal-applications", response_model=list[AdminPalApplicationOut])
def list_pal_applications() -> list[dict]:
    rows = (
        get_supabase_client()
        .table("players")
        .select(_PAL_APPLICATION_SELECT)
        .eq("status", "pending_review")
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return [_pal_application_out(row) for row in rows]


@router.patch("/pal-applications/{player_id}/status", response_model=AdminPalApplicationOut)
def update_pal_application_status(player_id: str, payload: AdminPalApplicationStatusIn) -> dict:
    client = get_supabase_client()
    existing = client.table("players").select("id").eq("id", player_id).maybe_single().execute()
    if not existing or not existing.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")

    client.table("players").update({"status": payload.status}).eq("id", player_id).execute()
    result = (
        client.table("players").select(_PAL_APPLICATION_SELECT).eq("id", player_id).single().execute()
    )
    return _pal_application_out(result.data)


# Flagged players ------------------------------------------------------------------------
# No auth dependency: `stores/admin.ts`'s mock-credential gate (`admin@squadup.gg`,
# session-only) is the only guard until real admin auth ships (per the 1.15 checkpoint note).


@router.patch("/players/{player_id}/ban", response_model=AdminFlaggedPlayerOut | None)
def set_player_banned(player_id: str, payload: AdminBanIn) -> dict | None:
    """Ban/unban toggle from the Flagged Players review modal (3.19) - a flag stays a
    moderation-queue label on its own (`update_flagged_player_status` above), this is the
    action that actually hides a Pal from Browse Players / their public profile
    (`routers/players.py`'s `is_banned` filters)."""
    client = get_supabase_client()
    existing = client.table("players").select("id").eq("id", player_id).maybe_single().execute()
    if not existing or not existing.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player not found")

    client.table("players").update({"is_banned": payload.is_banned}).eq("id", player_id).execute()

    # Return the caller's own flag row (if any) re-joined, so the Flagged Players panel can patch
    # its list in place the same way a status update does - a player can be banned with no flag
    # on file at all, in which case there's nothing to patch and the frontend just re-fetches.
    flag = (
        client.table("admin_flags")
        .select(_FLAG_SELECT)
        .eq("player_id", player_id)
        .order("created_at", desc=True)
        .limit(1)
        .maybe_single()
        .execute()
    )
    return _flag_out(flag.data) if flag and flag.data else None


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
        client.table("order_disputes")
        .select("id, status, refund_coins, booking_id, bookings(user_id)")
        .eq("id", dispute_id)
        .maybe_single()
        .execute()
    )
    if not existing or not existing.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dispute not found")

    update: dict = {"status": payload.status}
    if payload.status in ("resolved", "refunded"):
        update["resolved_at"] = datetime.now(UTC).isoformat()

    # Only credit on the open->refunded transition, not on a redundant re-click of "Refund" once
    # a dispute is already refunded - `refund_coins` is only ever set for a `full_refund` request
    # (`routers/bookings.py`'s `dispute_booking`), so a `partial_refund`/`reporting` dispute has
    # nothing to credit here until the admin UI grows a way to enter a partial amount.
    if payload.status == "refunded" and existing.data["status"] != "refunded":
        refund_coins = existing.data.get("refund_coins") or 0
        buyer_id = (existing.data.get("bookings") or {}).get("user_id")
        if refund_coins > 0 and buyer_id:
            adjust_coin_balance(
                client,
                buyer_id,
                refund_coins,
                kind="refund",
                label="Refund",
                detail="Dispute resolved",
                booking_id=existing.data["booking_id"],
            )

    client.table("order_disputes").update(update).eq("id", dispute_id).execute()
    result = (
        client.table("order_disputes")
        .select(_DISPUTE_SELECT)
        .eq("id", dispute_id)
        .single()
        .execute()
    )
    return _dispute_out(result.data)


# Overview -------------------------------------------------------------------------------
# Same no-auth posture as the sections above.


@router.get("/overview", response_model=AdminOverviewOut)
def get_overview() -> dict:
    client = get_supabase_client()

    total_users = client.table("users").select("id", count="exact", head=True).execute().count or 0
    total_pals = client.table("players").select("id", count="exact", head=True).execute().count or 0

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    orders_today = (
        client.table("bookings")
        .select("id", count="exact", head=True)
        .gte("created_at", today_start.isoformat())
        .execute()
        .count
        or 0
    )

    escrow_rows = (
        client.table("bookings")
        .select("total_coins")
        .in_("status", _ESCROW_STATUSES)
        .execute()
        .data
        or []
    )
    coins_in_escrow = sum(row["total_coins"] for row in escrow_rows)

    commission_rows = (
        client.table("bookings").select("commission_coins").eq("status", "completed").execute().data or []
    )
    total_commission_coins = sum(row["commission_coins"] for row in commission_rows)

    week_start = today_start.date() - timedelta(days=6)
    flag_rows = (
        client.table("admin_flags")
        .select("created_at")
        .gte("created_at", week_start.isoformat())
        .execute()
        .data
        or []
    )
    counts_by_day: dict[date, int] = defaultdict(int)
    for row in flag_rows:
        counts_by_day[datetime.fromisoformat(row["created_at"]).date()] += 1
    reports_this_week = [
        {
            "day": _WEEKDAY_LABELS[(week_start + timedelta(days=offset)).weekday()],
            "count": counts_by_day[week_start + timedelta(days=offset)],
        }
        for offset in range(7)
    ]

    return {
        "total_users": total_users,
        "total_pals": total_pals,
        "orders_today": orders_today,
        "coins_in_escrow": coins_in_escrow,
        "total_commission_coins": total_commission_coins,
        "reports_this_week": reports_this_week,
    }
