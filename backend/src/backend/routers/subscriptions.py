from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import get_current_user_id
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# Matches `SubscriptionModal.vue`'s `monthlyPriceCoins = 990` fallback, used when no service/
# price is passed. Quarterly is the modal's already-established 3x - 10% math.
DEFAULT_MONTHLY_PRICE_COINS = 990
BILLING_CYCLE_DAYS = {"monthly": 30, "quarterly": 90}


# Schemas ---------------------------------------------------------------------------------


class SubscriptionOut(CamelModel):
    id: str
    player_id: str
    player_display_name: str
    rating: float | None
    billing_cycle: str
    service_id: str | None
    service_label: str
    renews_on: str
    price_coins: int
    status: str


class SubscribeIn(CamelModel):
    player_id: str
    service_id: str | None = None
    billing_cycle: str = "monthly"


# Helpers -----------------------------------------------------------------------------------

_SELECT = "*, players(display_name, rating), services(name)"


def _subscription_out(row: dict) -> dict:
    player = row.get("players") or {}
    service = row.get("services") or {}
    return {
        **row,
        "player_display_name": player.get("display_name") or "Pal",
        "rating": player.get("rating"),
        "service_label": service.get("name") or "Subscription",
    }


def _fetch_subscription(client, subscription_id: str) -> dict:
    result = client.table("subscriptions").select(_SELECT).eq("id", subscription_id).single().execute()
    return result.data


def _get_owned_subscription(client, subscription_id: str, user_id: str) -> dict:
    result = (
        client.table("subscriptions")
        .select(_SELECT)
        .eq("id", subscription_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subscription not found")
    return result.data


# Routes ------------------------------------------------------------------------------------


@router.get("/mine", response_model=list[SubscriptionOut])
def list_my_subscriptions(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    rows = (
        get_supabase_client()
        .table("subscriptions")
        .select(_SELECT)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return [_subscription_out(row) for row in rows]


@router.post("", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def subscribe(payload: SubscribeIn, user_id: str = Depends(get_current_user_id)) -> dict:
    if payload.billing_cycle not in BILLING_CYCLE_DAYS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid billing cycle")

    client = get_supabase_client()
    player = client.table("players").select("id").eq("id", payload.player_id).maybe_single().execute()
    if not player or not player.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player not found")

    monthly_price = DEFAULT_MONTHLY_PRICE_COINS
    if payload.service_id:
        service = (
            client.table("services")
            .select("id, service_pricing_options(price_coins, sort_order)")
            .eq("id", payload.service_id)
            .eq("player_id", payload.player_id)
            .maybe_single()
            .execute()
        )
        if not service or not service.data:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
        pricing = sorted(service.data.get("service_pricing_options") or [], key=lambda p: p["sort_order"])
        if pricing:
            monthly_price = pricing[0]["price_coins"]

    price_coins = monthly_price if payload.billing_cycle == "monthly" else round(monthly_price * 3 * 0.9)
    renews_on = datetime.now(UTC).date() + timedelta(days=BILLING_CYCLE_DAYS[payload.billing_cycle])

    subscription_id = str(uuid4())
    client.table("subscriptions").insert(
        {
            "id": subscription_id,
            "user_id": user_id,
            "player_id": payload.player_id,
            "service_id": payload.service_id,
            "billing_cycle": payload.billing_cycle,
            "renews_on": renews_on.isoformat(),
            "price_coins": price_coins,
            "status": "active",
        }
    ).execute()

    return _subscription_out(_fetch_subscription(client, subscription_id))


@router.post("/{subscription_id}/cancel", response_model=SubscriptionOut)
def cancel_subscription(subscription_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    """Leaves `renews_on` as-is - the frontend already reads it as "access until" once
    cancelled, per `SubscriptionsView.vue`."""
    client = get_supabase_client()
    _get_owned_subscription(client, subscription_id, user_id)
    client.table("subscriptions").update({"status": "cancelled"}).eq("id", subscription_id).execute()
    return _subscription_out(_fetch_subscription(client, subscription_id))


@router.post("/{subscription_id}/resubscribe", response_model=SubscriptionOut)
def resubscribe(subscription_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    client = get_supabase_client()
    subscription = _get_owned_subscription(client, subscription_id, user_id)
    renews_on = datetime.now(UTC).date() + timedelta(days=BILLING_CYCLE_DAYS[subscription["billing_cycle"]])
    client.table("subscriptions").update({"status": "active", "renews_on": renews_on.isoformat()}).eq(
        "id", subscription_id
    ).execute()
    return _subscription_out(_fetch_subscription(client, subscription_id))
