import logging

from fastapi import APIRouter, Depends, HTTPException, status
from postgrest.exceptions import APIError
from pydantic import Field

from ..core.auth import get_current_user_id
from ..core.notify import notify
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


# Schemas ---------------------------------------------------------------------------------


class ReviewCreateIn(CamelModel):
    booking_id: str
    rating: int
    text: str | None = None
    highlights: list[str] = Field(default_factory=list)
    tip_coins: int = 0


class ReviewOut(CamelModel):
    id: str
    author: str
    rating: int
    text: str | None
    sentiment: str
    highlights: list[str]
    tip_coins: int
    created_at: str


# The "What went well?" chips in `LeaveReviewModal.vue`. Kept as a closed set rather than free
# text: these render on a Pal's public profile, so an arbitrary string posted straight to the API
# would be a way to put words on someone else's page.
HIGHLIGHT_OPTIONS = frozenset(
    {"On time", "Skilled", "Friendly", "Great comms", "Would rebook", "Patient"}
)


# Helpers -----------------------------------------------------------------------------------


def _sentiment_for(rating: int) -> str:
    if rating >= 4:
        return "positive"
    if rating == 3:
        return "neutral"
    return "negative"


# `submit_review`'s custom SQLSTATEs (see the 4.53 migration) mapped back to HTTP. Raising them
# from Postgres rather than pre-checking in Python is what lets the whole submission - review,
# rating recomputes, and both sides of the tip - be one transaction.
RPC_ERROR_STATUS = {
    "SU404": status.HTTP_404_NOT_FOUND,
    "SU409": status.HTTP_409_CONFLICT,
    "SU410": status.HTTP_409_CONFLICT,
    "SU411": status.HTTP_409_CONFLICT,
    "SU412": status.HTTP_409_CONFLICT,
}


# Create + read -------------------------------------------------------------------------------


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreateIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """The buyer's "Leave review" submission (`LeaveReviewModal`, My Bookings). An optional tip
    moves coins on top of the order the buyer already paid for: it debits them and credits the
    Pal as its own `tip` ledger line, so Wallet history reads as a tip rather than a second
    order against the same booking (4.44).

    The write itself is the `submit_review` transaction (4.53) - review, rating recomputes and
    both sides of the tip commit together, so a dropped connection can never leave a review
    standing with the tip half-paid and the buyer locked out of retrying."""
    if not 1 <= payload.rating <= 5:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Rating must be between 1 and 5")
    if payload.tip_coins < 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Tip can't be negative")
    unknown = [h for h in payload.highlights if h not in HIGHLIGHT_OPTIONS]
    if unknown:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown highlight: {unknown[0]}")
    # Order preserved, duplicates dropped - the modal can't send one twice, but the API is public.
    highlights = list(dict.fromkeys(payload.highlights))

    client = get_supabase_client()
    booking = (
        client.table("bookings")
        .select("service_id, player_id")
        .eq("id", payload.booking_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not booking or not booking.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")

    # Read only for the notification text and the tip's ledger `detail`; `submit_review` re-reads
    # and re-checks everything it acts on inside the transaction.
    user = client.table("users").select("display_name").eq("id", user_id).maybe_single().execute()
    author = ((user.data or {}).get("display_name") if user else None) or "Buyer"

    service = client.table("services").select("name").eq("id", booking.data["service_id"]).maybe_single().execute()
    service_name = ((service.data or {}).get("name") if service else None) or "a service"

    try:
        review_id = client.rpc(
            "submit_review",
            {
                "p_booking_id": payload.booking_id,
                "p_user_id": user_id,
                "p_rating": payload.rating,
                "p_text": payload.text,
                "p_sentiment": _sentiment_for(payload.rating),
                "p_highlights": highlights,
                "p_tip_coins": payload.tip_coins,
                "p_tip_detail": service_name,
                "p_tip_from": f"From {author}",
            },
        ).execute().data
    except APIError as exc:
        http_status = RPC_ERROR_STATUS.get(exc.code or "")
        if http_status is None:
            raise
        raise HTTPException(http_status, exc.message) from exc

    # Past the commit: the review and the tip are already durable, so a dropped connection here
    # must not come back to the buyer as a failed submission - they'd retry into a 409 while
    # their coins had in fact moved. A missing notification is the cheaper loss.
    try:
        player = (
            client.table("players")
            .select("user_id")
            .eq("id", booking.data["player_id"])
            .maybe_single()
            .execute()
        )
        pal_user_id = (player.data or {}).get("user_id") if player else None
        if pal_user_id:
            message = f"{author} left you a {payload.rating}-star review on {service_name}."
            if payload.tip_coins > 0:
                message = (
                    f"{author} left you a {payload.rating}-star review on {service_name} "
                    f"and tipped {payload.tip_coins} SC."
                )
            notify(pal_user_id, "review", message)
    except Exception:
        logger.exception("Review %s committed but notifying the Pal failed", review_id)

    row = client.table("reviews").select("*").eq("id", review_id).single().execute().data
    return {**row, "author": author}


@router.get("/player/{player_id}", response_model=dict[str, list[ReviewOut]])
def list_player_reviews(player_id: str) -> dict:
    """Player Profile's Services tab - reviews grouped by `service_id`, matching the frontend's
    `PlayerProfile.reviews: Record<string, PlayerReview[]>` shape."""
    client = get_supabase_client()
    service_ids = [
        s["id"] for s in client.table("services").select("id").eq("player_id", player_id).execute().data or []
    ]
    if not service_ids:
        return {}

    rows = (
        client.table("reviews")
        .select("*, users(display_name)")
        .in_("service_id", service_ids)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        author = (row.get("users") or {}).get("display_name") or "Buyer"
        grouped.setdefault(row["service_id"], []).append({**row, "author": author})
    return grouped
