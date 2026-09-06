from uuid import uuid4

import stripe
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import get_current_user_id
from ..core.config import get_settings
from ..core.notify import notify
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/wallet", tags=["wallet"])

# Matches `mocks/wallet.ts`'s `mockWithdrawalPlatformFeePct`, applied on the backend side too
# since the frontend's fee preview must match what a real withdrawal actually charges.
WITHDRAWAL_FEE_PCT = 10


# Schemas ---------------------------------------------------------------------------------


class TopupPackageOut(CamelModel):
    id: str
    coins: int
    price_usd: float
    bonus_coins: int
    is_base_rate: bool


class WalletActivityOut(CamelModel):
    id: str
    kind: str
    status: str
    label: str
    detail: str | None
    coins: int
    created_at: str


class WalletOut(CamelModel):
    balance_coins: int
    pending_clearance_coins: int
    activity: list[WalletActivityOut]


class TopupPaymentIntentIn(CamelModel):
    package_id: str


class TopupPaymentIntentOut(CamelModel):
    client_secret: str
    payment_intent_id: str


class TopupIn(CamelModel):
    package_id: str
    payment_intent_id: str


class PayoutMethodOut(CamelModel):
    id: str
    brand: str
    label: str
    detail: str | None
    is_default: bool


class WithdrawalOut(CamelModel):
    id: str
    coins: int
    fee_coins: int
    status: str
    created_at: str
    payout_method_id: str | None


class WithdrawalCreateIn(CamelModel):
    coins: int
    payout_method_id: str | None = None


# Helpers -----------------------------------------------------------------------------------


def _get_owned_player(user_id: str) -> dict:
    result = get_supabase_client().table("players").select("id").eq("user_id", user_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Player profile not found")
    return result.data


def _pending_clearance_coins(client, player_id: str) -> int:
    """Coins tied up in orders a Pal has accepted but not yet completed - not available to
    withdraw yet, mirrors `mocks/wallet.ts`'s `mockPendingCoins`."""
    rows = (
        client.table("bookings")
        .select("total_coins")
        .eq("player_id", player_id)
        .eq("status", "accepted")
        .execute()
        .data
        or []
    )
    return sum(row["total_coins"] for row in rows)


def _record_transaction(
    client,
    user_id: str,
    *,
    kind: str,
    label: str,
    detail: str | None,
    coins: int,
    txn_status: str = "completed",
    stripe_payment_intent_id: str | None = None,
) -> None:
    client.table("wallet_transactions").insert(
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "kind": kind,
            "status": txn_status,
            "label": label,
            "detail": detail,
            "coins": coins,
            "stripe_payment_intent_id": stripe_payment_intent_id,
        }
    ).execute()


def _get_wallet(user_id: str) -> dict:
    client = get_supabase_client()
    user = client.table("users").select("coin_balance").eq("id", user_id).maybe_single().execute()
    if not user or not user.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    player = client.table("players").select("id").eq("user_id", user_id).maybe_single().execute()
    pending = _pending_clearance_coins(client, player.data["id"]) if player and player.data else 0

    activity = (
        client.table("wallet_transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )
    return {
        "balance_coins": user.data["coin_balance"],
        "pending_clearance_coins": pending,
        "activity": activity,
    }


# Wallet ------------------------------------------------------------------------------------


@router.get("/me", response_model=WalletOut)
def get_my_wallet(user_id: str = Depends(get_current_user_id)) -> dict:
    return _get_wallet(user_id)


@router.get("/topup-packages", response_model=list[TopupPackageOut])
def list_topup_packages() -> list[dict]:
    """Public, matches `mocks/wallet.ts`'s `mockTopUpPackages` - real rows seeded in 3.9b since
    the 2.3 migration created `topup_packages` with no data."""
    return get_supabase_client().table("topup_packages").select("*").order("price_usd").execute().data or []


@router.post("/topup/payment-intent", response_model=TopupPaymentIntentOut, status_code=status.HTTP_201_CREATED)
def create_topup_payment_intent(payload: TopupPaymentIntentIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """4.1c: creates a Stripe PaymentIntent for the chosen package's dollar amount - the frontend
    confirms it client-side with Stripe Elements (a card form embedded on `/wallet`, same pattern
    as PawMart's `POST /payment-intent`), then calls `POST /topup` with the resulting
    `payment_intent_id`. Nothing is credited here; that endpoint verifies the charge actually
    succeeded before crediting anything."""
    client = get_supabase_client()
    package = client.table("topup_packages").select("*").eq("id", payload.package_id).maybe_single().execute()
    if not package or not package.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Top-up package not found")

    stripe.api_key = get_settings().stripe_secret_key
    intent = stripe.PaymentIntent.create(
        amount=round(package.data["price_usd"] * 100),
        currency="usd",
        payment_method_types=["card"],
        metadata={"user_id": user_id, "package_id": payload.package_id},
    )
    return {"client_secret": intent.client_secret, "payment_intent_id": intent.id}


@router.post("/topup", response_model=WalletOut, status_code=status.HTTP_201_CREATED)
def top_up(payload: TopupIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """4.1d: the only place a top-up actually gets credited. Re-verifies the PaymentIntent
    server-side against the Stripe API (status/amount/who it belongs to) rather than trusting the
    client's word that payment succeeded - a client hitting this endpoint proves nothing on its
    own, that was the old mock `POST /topup`'s exact flaw."""
    client = get_supabase_client()
    package = client.table("topup_packages").select("*").eq("id", payload.package_id).maybe_single().execute()
    if not package or not package.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Top-up package not found")

    stripe.api_key = get_settings().stripe_secret_key
    try:
        intent = stripe.PaymentIntent.retrieve(payload.payment_intent_id)
    except stripe.error.StripeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid payment intent") from exc

    # StripeObject has no .get() - only __getitem__/__contains__, same gotcha PawMart hit.
    intent_user_id = intent.metadata["user_id"] if "user_id" in intent.metadata else None  # noqa: SIM401
    if intent_user_id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your payment")
    if intent.status != "succeeded":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment has not succeeded")
    if intent.amount != round(package.data["price_usd"] * 100):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment amount does not match package price")

    user = client.table("users").select("coin_balance").eq("id", user_id).maybe_single().execute()
    if not user or not user.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    coins = package.data["coins"] + package.data["bonus_coins"]
    try:
        # Unique constraint on `stripe_payment_intent_id` (4.1b) rejects a second top-up for the
        # same PaymentIntent - the idempotency guard against a double-submitted confirm.
        _record_transaction(
            client,
            user_id,
            kind="topup",
            label="Top-up",
            detail="Visa",
            coins=coins,
            stripe_payment_intent_id=payload.payment_intent_id,
        )
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This payment has already been used") from exc

    client.table("users").update({"coin_balance": user.data["coin_balance"] + coins}).eq("id", user_id).execute()

    return _get_wallet(user_id)


# Payout methods ------------------------------------------------------------------------------
# Read-only: no create/delete route, "+ Add payout method" stays a disabled stub on both pages
# since no add-method form exists in any mockup, same convention as 3.1i's "Edit".


@router.get("/payout-methods", response_model=list[PayoutMethodOut])
def list_payout_methods(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    player = _get_owned_player(user_id)
    return (
        get_supabase_client()
        .table("payout_methods")
        .select("*")
        .eq("player_id", player["id"])
        .order("created_at")
        .execute()
        .data
        or []
    )


# Withdrawals ---------------------------------------------------------------------------------


@router.get("/withdrawals", response_model=list[WithdrawalOut])
def list_withdrawals(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    player = _get_owned_player(user_id)
    return (
        get_supabase_client()
        .table("withdrawals")
        .select("*")
        .eq("player_id", player["id"])
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )


@router.post("/withdrawals", response_model=WithdrawalOut, status_code=status.HTTP_201_CREATED)
def create_withdrawal(payload: WithdrawalCreateIn, user_id: str = Depends(get_current_user_id)) -> dict:
    if payload.coins <= 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Withdrawal amount must be positive")

    client = get_supabase_client()
    player = _get_owned_player(user_id)
    user = client.table("users").select("coin_balance").eq("id", user_id).maybe_single().execute()
    if not user or not user.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    available = user.data["coin_balance"] - _pending_clearance_coins(client, player["id"])
    if payload.coins > available:
        raise HTTPException(status.HTTP_409_CONFLICT, "Withdrawal amount exceeds available balance")

    if payload.payout_method_id:
        method = (
            client.table("payout_methods")
            .select("id")
            .eq("id", payload.payout_method_id)
            .eq("player_id", player["id"])
            .maybe_single()
            .execute()
        )
        if not method or not method.data:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Payout method not found")

    fee_coins = round(payload.coins * WITHDRAWAL_FEE_PCT / 100)
    withdrawal_id = str(uuid4())
    client.table("withdrawals").insert(
        {
            "id": withdrawal_id,
            "player_id": player["id"],
            "payout_method_id": payload.payout_method_id,
            "coins": payload.coins,
            "fee_coins": fee_coins,
            "status": "in_progress",
        }
    ).execute()
    client.table("users").update({"coin_balance": user.data["coin_balance"] - payload.coins}).eq(
        "id", user_id
    ).execute()
    _record_transaction(
        client,
        user_id,
        kind="payout",
        label="Withdrawal",
        detail=None,
        coins=-payload.coins,
        txn_status="pending",
    )
    notify(user_id, "payout", f"Withdrawal of {payload.coins} SC requested. It's now processing.")

    return client.table("withdrawals").select("*").eq("id", withdrawal_id).single().execute().data
