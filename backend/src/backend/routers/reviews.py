from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import get_current_user_id
from ..core.notify import notify
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/reviews", tags=["reviews"])


# Schemas ---------------------------------------------------------------------------------


class ReviewCreateIn(CamelModel):
    booking_id: str
    rating: int
    text: str | None = None


class ReviewOut(CamelModel):
    id: str
    author: str
    rating: int
    text: str | None
    sentiment: str
    created_at: str


# Helpers -----------------------------------------------------------------------------------


def _sentiment_for(rating: int) -> str:
    if rating >= 4:
        return "positive"
    if rating == 3:
        return "neutral"
    return "negative"


def _recompute_rating(client, table: str, id_field: str, row_id: str, ratings: list[int]) -> None:
    avg = round(sum(ratings) / len(ratings), 2) if ratings else None
    client.table(table).update({"rating": avg}).eq(id_field, row_id).execute()


def _recompute_after_review(client, service_id: str, player_id: str) -> None:
    """Reviews are keyed by `service_id`, but a Pal's headline `rating`/`review_count` (shown on
    browse cards and the profile header) aggregate across every one of their services - so both
    need recomputing whenever a review lands."""
    service_ratings = [
        r["rating"] for r in client.table("reviews").select("rating").eq("service_id", service_id).execute().data or []
    ]
    _recompute_rating(client, "services", "id", service_id, service_ratings)

    service_ids = [s["id"] for s in client.table("services").select("id").eq("player_id", player_id).execute().data or []]
    player_ratings = (
        client.table("reviews").select("rating").in_("service_id", service_ids).execute().data or [] if service_ids else []
    )
    ratings = [r["rating"] for r in player_ratings]
    avg = round(sum(ratings) / len(ratings), 2) if ratings else None
    client.table("players").update({"rating": avg, "review_count": len(ratings)}).eq("id", player_id).execute()


# Create + read -------------------------------------------------------------------------------


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreateIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """The buyer's "Leave review" submission (`LeaveReviewModal`, My Bookings). `highlights`/
    `tipCoins` collected by that modal stay UI-only for now - `reviews` (2.3) has no matching
    columns, and tips need the wallet ledger (3.9), same "stays UI-only" convention as Create
    Service's Category field."""
    if not 1 <= payload.rating <= 5:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Rating must be between 1 and 5")

    client = get_supabase_client()
    booking = (
        client.table("bookings")
        .select("id, user_id, service_id, player_id, status")
        .eq("id", payload.booking_id)
        .maybe_single()
        .execute()
    )
    if not booking or not booking.data or booking.data["user_id"] != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    if booking.data["status"] != "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Order must be completed before it can be reviewed")

    existing = client.table("reviews").select("id").eq("booking_id", payload.booking_id).maybe_single().execute()
    if existing and existing.data:
        raise HTTPException(status.HTTP_409_CONFLICT, "This order has already been reviewed")

    user = client.table("users").select("display_name").eq("id", user_id).maybe_single().execute()
    author = ((user.data or {}).get("display_name") if user else None) or "Buyer"

    review_id = str(uuid4())
    client.table("reviews").insert(
        {
            "id": review_id,
            "service_id": booking.data["service_id"],
            "booking_id": payload.booking_id,
            "author_id": user_id,
            "rating": payload.rating,
            "text": payload.text,
            "sentiment": _sentiment_for(payload.rating),
        }
    ).execute()

    _recompute_after_review(client, booking.data["service_id"], booking.data["player_id"])

    player = (
        client.table("players")
        .select("user_id, display_name")
        .eq("id", booking.data["player_id"])
        .maybe_single()
        .execute()
    )
    pal_user_id = (player.data or {}).get("user_id") if player else None

    service = client.table("services").select("name").eq("id", booking.data["service_id"]).maybe_single().execute()
    service_name = ((service.data or {}).get("name") if service else None) or "a service"

    if pal_user_id:
        notify(pal_user_id, "review", f"{author} left you a {payload.rating}-star review on {service_name}.")

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
