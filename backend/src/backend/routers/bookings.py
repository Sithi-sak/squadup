import random
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field

from ..core.auth import get_current_user_id
from ..core.notify import notify
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/bookings", tags=["bookings"])


# Schemas ---------------------------------------------------------------------------------


class BookingAddonIn(CamelModel):
    label: str
    price_coins: int


class BookingAddonOut(CamelModel):
    id: str
    label: str
    price_coins: int


class BookingCreateIn(CamelModel):
    player_id: str
    service_id: str
    service_type_label: str
    price_coins: int
    price_unit: str
    quantity: int = 1
    addons: list[BookingAddonIn] = Field(default_factory=list)
    promo_label: str | None = None
    subtotal_coins: int
    addons_coins: int = 0
    discount_coins: int = 0
    total_coins: int
    payment_method: str = "coins"
    scheduled_for: str | None = None


class CancelIn(CamelModel):
    reason: str
    refund_option: str
    refund_coins: int = 0
    note: str | None = None


class DisputeIn(CamelModel):
    reason: str
    outcome: str
    note: str | None = None


class BookingOut(CamelModel):
    id: str
    order_number: str
    player_id: str
    player_display_name: str
    player_avatar_url: str | None
    service_id: str
    service_name: str
    service_type_label: str
    user_id: str
    buyer_display_name: str
    status: str
    price_coins: int
    price_unit: str
    quantity: int
    addons: list[BookingAddonOut]
    promo_label: str | None
    subtotal_coins: int
    addons_coins: int
    discount_coins: int
    total_coins: int
    payment_method: str
    scheduled_for: str | None
    created_at: str
    has_review: bool


# Helpers -----------------------------------------------------------------------------------

_SELECT = (
    "*, players(display_name, avatar_url, user_id), services(name), users(display_name), "
    "booking_addons(id, label, price_coins), reviews(id)"
)

_OUTCOME_MAP = {"full": "full_refund", "partial": "partial_refund", "reporting": "reporting"}


def _booking_out(row: dict) -> dict:
    player = row.get("players") or {}
    service = row.get("services") or {}
    buyer = row.get("users") or {}
    return {
        **row,
        "player_display_name": player.get("display_name") or "Pal",
        "player_avatar_url": player.get("avatar_url"),
        "service_name": service.get("name") or row["service_type_label"],
        "buyer_display_name": buyer.get("display_name") or "Buyer",
        "addons": row.get("booking_addons") or [],
        "has_review": bool(row.get("reviews")),
    }


def _booking_names(row: dict) -> tuple[str, str, str | None, str]:
    """(pal_name, buyer_name, pal_user_id, service_name) for building notification copy. Seed
    Pals have no `players.user_id` (2.3 note), so `pal_user_id` is `None` when there's nobody
    real to notify."""
    player = row.get("players") or {}
    service = row.get("services") or {}
    buyer = row.get("users") or {}
    pal_name = player.get("display_name") or "Your Pal"
    buyer_name = buyer.get("display_name") or "A buyer"
    service_name = service.get("name") or row["service_type_label"]
    return pal_name, buyer_name, player.get("user_id"), service_name


def _fetch_booking(client, booking_id: str) -> dict:
    result = client.table("bookings").select(_SELECT).eq("id", booking_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return result.data


def _get_my_player_id(client, user_id: str) -> str | None:
    result = client.table("players").select("id").eq("user_id", user_id).maybe_single().execute()
    return result.data["id"] if result and result.data else None


def _get_owned_booking(client, booking_id: str, user_id: str) -> dict:
    """A booking reachable by whoever is party to it: the buyer (`user_id`) or the Pal
    fulfilling it (`players.user_id`)."""
    booking = _fetch_booking(client, booking_id)
    player_id = _get_my_player_id(client, user_id)
    if booking["user_id"] != user_id and booking["player_id"] != player_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return booking


def _require_pal_booking(client, booking_id: str, user_id: str, *, expected_status: str) -> dict:
    player_id = _get_my_player_id(client, user_id)
    booking = _fetch_booking(client, booking_id)
    if not player_id or booking["player_id"] != player_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    if booking["status"] != expected_status:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Order is not {expected_status}")
    return booking


def _generate_order_number(client) -> str:
    for _ in range(5):
        candidate = f"SQ-{random.randint(10000, 99999)}"
        existing = client.table("bookings").select("id").eq("order_number", candidate).maybe_single().execute()
        if not existing or not existing.data:
            return candidate
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not generate order number")


def _resolve_addon_id(client, label: str, price_coins: int) -> str:
    """Add-ons are still a flat, unauthored catalog (`mocks/bookings.ts`'s `mockAddons` on the
    frontend - see CHECKPOINT.md's Booking flow note), so there's no admin flow to pre-seed
    `addons` rows. Look one up by label, self-healing by inserting it the first time it's seen."""
    existing = client.table("addons").select("id").eq("label", label).maybe_single().execute()
    if existing and existing.data:
        return existing.data["id"]
    created = client.table("addons").insert({"label": label, "price_coins": price_coins}).execute()
    return created.data[0]["id"]


# Create + read -------------------------------------------------------------------------------


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreateIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """The buyer's "Place order" submission (Checkout). Note this is only called once Checkout
    actually submits, not when the "Book a session" modal's "Continue to checkout" fires - that
    stays a client-side draft (`stores/bookings.ts`'s `draft`) so an abandoned checkout never
    creates a real `pending` row, resolving the draft-vs-submitted question left open in
    CHECKPOINT.md's Booking flow note."""
    client = get_supabase_client()

    service = client.table("services").select("id, player_id").eq("id", payload.service_id).maybe_single().execute()
    if not service or not service.data or service.data["player_id"] != payload.player_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")

    booking_id = str(uuid4())
    order_number = _generate_order_number(client)

    client.table("bookings").insert(
        {
            "id": booking_id,
            "order_number": order_number,
            "player_id": payload.player_id,
            "service_id": payload.service_id,
            "user_id": user_id,
            "status": "pending",
            "service_type_label": payload.service_type_label,
            "price_coins": payload.price_coins,
            "price_unit": payload.price_unit,
            "quantity": payload.quantity,
            "promo_label": payload.promo_label,
            "subtotal_coins": payload.subtotal_coins,
            "addons_coins": payload.addons_coins,
            "discount_coins": payload.discount_coins,
            "total_coins": payload.total_coins,
            "payment_method": payload.payment_method,
            "scheduled_for": payload.scheduled_for,
        }
    ).execute()

    for addon in payload.addons:
        addon_id = _resolve_addon_id(client, addon.label, addon.price_coins)
        client.table("booking_addons").insert(
            {
                "booking_id": booking_id,
                "addon_id": addon_id,
                "label": addon.label,
                "price_coins": addon.price_coins,
            }
        ).execute()

    created = _fetch_booking(client, booking_id)
    _, buyer_name, pal_user_id, service_name = _booking_names(created)
    if pal_user_id:
        notify(pal_user_id, "booking", f"{buyer_name} requested to book {service_name}.")
    return _booking_out(created)


@router.get("/mine", response_model=list[BookingOut])
def list_my_bookings(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    """My Bookings (buyer side)."""
    client = get_supabase_client()
    rows = (
        client.table("bookings")
        .select(_SELECT)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return [_booking_out(row) for row in rows]


@router.get("/incoming", response_model=list[BookingOut])
def list_incoming_bookings(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    """Pal Dashboard / Orders (Pal side). Empty list rather than a 404 for an account with no
    Pal profile yet, since a plain user simply has no incoming orders."""
    client = get_supabase_client()
    player_id = _get_my_player_id(client, user_id)
    if not player_id:
        return []
    rows = (
        client.table("bookings")
        .select(_SELECT)
        .eq("player_id", player_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return [_booking_out(row) for row in rows]


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    return _booking_out(_get_owned_booking(client, booking_id, user_id))


# Status transitions ----------------------------------------------------------------------


@router.post("/{booking_id}/accept", response_model=BookingOut)
def accept_booking(booking_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _require_pal_booking(client, booking_id, user_id, expected_status="pending")
    client.table("bookings").update({"status": "accepted"}).eq("id", booking_id).execute()
    updated = _fetch_booking(client, booking_id)
    pal_name, _, _, service_name = _booking_names(updated)
    notify(updated["user_id"], "booking", f"{pal_name} accepted your booking for {service_name}.")
    return _booking_out(updated)


@router.post("/{booking_id}/decline", response_model=BookingOut)
def decline_booking(booking_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _require_pal_booking(client, booking_id, user_id, expected_status="pending")
    client.table("bookings").update({"status": "declined"}).eq("id", booking_id).execute()
    updated = _fetch_booking(client, booking_id)
    pal_name, _, _, service_name = _booking_names(updated)
    notify(updated["user_id"], "booking", f"{pal_name} declined your booking for {service_name}.")
    return _booking_out(updated)


@router.post("/{booking_id}/complete", response_model=BookingOut)
def complete_booking(booking_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    _require_pal_booking(client, booking_id, user_id, expected_status="accepted")
    client.table("bookings").update({"status": "completed"}).eq("id", booking_id).execute()
    updated = _fetch_booking(client, booking_id)
    pal_name, _, _, service_name = _booking_names(updated)
    notify(updated["user_id"], "booking", f"Your session for {service_name} with {pal_name} is complete.")
    return _booking_out(updated)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: str, payload: CancelIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """Reachable by either party (`CancelOrderModal` is currently only wired up on the buyer's
    My Bookings / Order Detail pages, but the reason list reads Pal-authored - see
    `components/modals/CancelOrderModal.vue` - so this doesn't assume which side is cancelling)."""
    client = get_supabase_client()
    booking = _get_owned_booking(client, booking_id, user_id)
    if booking["status"] not in ("pending", "accepted"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Order can no longer be cancelled")

    client.table("order_cancellations").insert(
        {
            "booking_id": booking_id,
            "cancelled_by": user_id,
            "reason": payload.reason,
            "refund_option": payload.refund_option,
            "refund_coins": payload.refund_coins,
            "note": payload.note,
        }
    ).execute()
    client.table("bookings").update({"status": "declined"}).eq("id", booking_id).execute()
    updated = _fetch_booking(client, booking_id)
    pal_name, buyer_name, pal_user_id, service_name = _booking_names(updated)
    if user_id == updated["user_id"]:
        # the buyer cancelled - notify the Pal
        if pal_user_id:
            notify(pal_user_id, "booking", f"{buyer_name} cancelled the booking for {service_name}.")
    else:
        # the Pal cancelled - notify the buyer
        notify(updated["user_id"], "booking", f"{pal_name} cancelled the booking for {service_name}.")
    return _booking_out(updated)


@router.post("/{booking_id}/dispute", status_code=status.HTTP_201_CREATED)
def dispute_booking(booking_id: str, payload: DisputeIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """Buyer's "Report an issue" (`RefundModal`). Backs both that flow and the admin Disputes tab
    - see CHECKPOINT.md's 2.3 note on `order_disputes`."""
    client = get_supabase_client()
    booking = _fetch_booking(client, booking_id)
    if booking["user_id"] != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")

    requested_outcome = _OUTCOME_MAP.get(payload.outcome, "reporting")
    client.table("order_disputes").insert(
        {
            "booking_id": booking_id,
            "reported_by": user_id,
            "reason": payload.reason,
            "requested_outcome": requested_outcome,
            "refund_coins": booking["total_coins"] if requested_outcome == "full_refund" else None,
            "note": payload.note,
        }
    ).execute()
    return {"status": "submitted"}
