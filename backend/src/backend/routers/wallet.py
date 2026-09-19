from datetime import UTC, datetime, timedelta
from uuid import uuid4

import stripe
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import get_current_user_id
from ..core.config import get_settings
from ..core.notify import notify
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/wallet", tags=["wallet"])

# SquadUp's cut of a payout (4.28c): the Pal keeps 80%, the platform takes 20%. Matches
# `mocks/wallet.ts`'s `mockWithdrawalPlatformFeePct`, applied on the backend side too since the
# frontend's fee preview must match what a real withdrawal actually charges.
WITHDRAWAL_FEE_PCT = 20

# Card and bank transfer only, and bank transfer means ABA (user request, 4.30) - the bank is not
# a free-text field, so nothing needs to carry its name in from the client. These are the two
# *categories* a client may ask for; what gets stored in `payout_methods.brand` for a card is the
# detected network (4.32), matching `payment_cards.brand`'s existing 'visa'-style values.
_PAYOUT_BRANDS = ("card", "bank")
_ABA_BANK_NAME = "ABA Bank"

# Only Visa and Mastercard have an icon in `assets/`, so every other network stores the generic
# 'card' and renders the fallback glyph rather than being mislabelled as one of these two.
_CARD_NETWORKS = {"visa": "Visa", "mastercard": "Mastercard", "card": "Card"}

# A payout request that is still waiting on, or in the middle of, an admin decision. Its coins are
# held out of the withdrawable balance but not debited yet (4.31).
_OPEN_WITHDRAWAL_STATUSES = ("requested", "in_progress")

# 4.4: registering for real Bakong KHQR access is out of scope for this project, so "QR Scan"
# simulates the KHQR UX instead - a session auto-confirms itself after KHQR_AUTO_CONFIRM_SECONDS
# rather than waiting on a real bank webhook, standing in for the judge/phone "scanning" it. State
# only needs to survive one demo session, so an in-memory dict (not a table) is enough.
KHQR_AUTO_CONFIRM_SECONDS = 5
KHQR_SESSION_TTL_SECONDS = 120
_khqr_sessions: dict[str, dict] = {}


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
    locked_payout_coins: int
    activity: list[WalletActivityOut]


class TopupPaymentIntentIn(CamelModel):
    package_id: str


class TopupPaymentIntentOut(CamelModel):
    client_secret: str
    payment_intent_id: str


class TopupIn(CamelModel):
    package_id: str
    payment_intent_id: str


class KhqrSessionOut(CamelModel):
    session_id: str
    qr_payload: str
    amount_usd: float
    expires_in_seconds: int


class KhqrStatusOut(CamelModel):
    status: str


class PayoutMethodOut(CamelModel):
    id: str
    brand: str
    label: str
    detail: str | None
    is_default: bool


class PayoutMethodCreateIn(CamelModel):
    brand: str
    account: str
    is_default: bool = False


class WithdrawalOut(CamelModel):
    id: str
    reference: str | None = None
    coins: int
    fee_coins: int
    status: str
    created_at: str
    reviewed_at: str | None = None
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


def _digits(account: str) -> str:
    """Card and account numbers are routinely typed with spaces or dashes - they carry no meaning
    here, so they are stripped before validating or masking."""
    return "".join(ch for ch in account if ch.isdigit())


def _luhn_ok(digits: str) -> bool:
    """The check digit every real card number carries. It catches a typo or an invented number
    like 1111111111111111, which used to be accepted (4.32) - it does not prove the card exists,
    and nothing here can, since no network is ever contacted."""
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _card_network(digits: str) -> str:
    """Network from the issuer prefix, the same ranges a card form uses to swap its icon while
    you type. Unrecognised prefixes fall back to the generic 'card'."""
    if digits.startswith("4"):
        return "visa"
    two, four = digits[:2], digits[:4]
    if two.isdigit() and 51 <= int(two) <= 55:
        return "mastercard"
    if four.isdigit() and 2221 <= int(four) <= 2720:
        return "mastercard"
    return "card"


def _mask_account(brand: str, account: str) -> tuple[str, str, str]:
    """Builds the `(stored_brand, label, detail)` a payout method is displayed by. Only the last
    four digits are ever stored - nothing here needs the full number back, and the
    Withdraw/Settings rows only render `detail`, so keeping the raw value would be storing a
    secret for no reader."""
    digits = _digits(account)
    last4 = digits[-4:]
    if brand != "card":
        return "bank", _ABA_BANK_NAME, f"•••• {last4}"
    network = _card_network(digits)
    return network, _CARD_NETWORKS[network], f"•••• {last4}"


def _get_owned_payout_method(player_id: str, method_id: str) -> dict:
    result = (
        get_supabase_client()
        .table("payout_methods")
        .select("*")
        .eq("id", method_id)
        .eq("player_id", player_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payout method not found")
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


def _payout_reference() -> str:
    """Short, quotable payout reference (`PO-4F2A9C31`). Unique-indexed, so the astronomically
    unlikely collision surfaces as an error rather than two payouts sharing a reference."""
    return f"PO-{uuid4().hex[:8].upper()}"


def _locked_payout_coins(client, player_id: str) -> int:
    """Coins spoken for by payout requests an admin has not decided yet. 4.31 moved the actual
    debit to approval time, so without this a Pal could queue up five full-balance requests, or
    spend the coins out from under a request while it sat in the queue, and approval would then
    try to debit money that is no longer there."""
    rows = (
        client.table("withdrawals")
        .select("coins")
        .eq("player_id", player_id)
        .in_("status", _OPEN_WITHDRAWAL_STATUSES)
        .execute()
        .data
        or []
    )
    return sum(row["coins"] for row in rows)


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
    withdrawal_id: str | None = None,
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
            "withdrawal_id": withdrawal_id,
        }
    ).execute()


def _get_wallet(user_id: str) -> dict:
    client = get_supabase_client()
    user = client.table("users").select("coin_balance").eq("id", user_id).maybe_single().execute()
    if not user or not user.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    player = client.table("players").select("id").eq("user_id", user_id).maybe_single().execute()
    has_player = bool(player and player.data)
    pending = _pending_clearance_coins(client, player.data["id"]) if has_player else 0
    locked_payout = _locked_payout_coins(client, player.data["id"]) if has_player else 0

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
        "locked_payout_coins": locked_payout,
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


@router.post("/topup/khqr", response_model=KhqrSessionOut, status_code=status.HTTP_201_CREATED)
def create_khqr_session(payload: TopupPaymentIntentIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """4.4b: fake KHQR "Scan to Pay" session for the chosen package - no Stripe/Bakong call at
    all, just a timer the frontend polls via `GET /topup/khqr/{id}/status`."""
    client = get_supabase_client()
    package = client.table("topup_packages").select("*").eq("id", payload.package_id).maybe_single().execute()
    if not package or not package.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Top-up package not found")

    now = datetime.now(UTC)
    session_id = str(uuid4())
    _khqr_sessions[session_id] = {
        "user_id": user_id,
        "amount_usd": package.data["price_usd"],
        "coins": package.data["coins"] + package.data["bonus_coins"],
        "status": "pending",
        "confirm_at": now + timedelta(seconds=KHQR_AUTO_CONFIRM_SECONDS),
        "expires_at": now + timedelta(seconds=KHQR_SESSION_TTL_SECONDS),
    }
    # Short and low-entropy on purpose - `session_id` already carries the real reference for the
    # status/complete calls, this string only needs to look plausible in the rendered QR. A long
    # payload (e.g. a full UUID) forces a higher QR version, i.e. a denser grid of small modules;
    # keeping this short lets the frontend pin a low version for a bigger-block look.
    qr_payload = f"KHQR|SquadUp|{package.data['price_usd']:.2f}|{session_id[:8]}"
    return {
        "session_id": session_id,
        "qr_payload": qr_payload,
        "amount_usd": package.data["price_usd"],
        "expires_in_seconds": KHQR_SESSION_TTL_SECONDS,
    }


@router.get("/topup/khqr/{session_id}/status", response_model=KhqrStatusOut)
def get_khqr_status(session_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    """4.4c: the frontend polls this while the QR modal is open. Flips `pending` -> `confirmed`
    once `confirm_at` has passed - standing in for the bank webhook a real KHQR integration would
    wait on - or -> `expired` if nobody "scanned" it in time."""
    session = _khqr_sessions.get(session_id)
    if not session or session["user_id"] != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "KHQR session not found")

    now = datetime.now(UTC)
    if session["status"] == "pending" and now >= session["expires_at"]:
        session["status"] = "expired"
    elif session["status"] == "pending" and now >= session["confirm_at"]:
        session["status"] = "confirmed"
    return {"status": session["status"]}


@router.post("/topup/khqr/{session_id}/complete", response_model=WalletOut, status_code=status.HTTP_201_CREATED)
def complete_khqr_topup(session_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    """4.4d: the actual credit, only once the session has reached `confirmed` - same
    verify-before-credit shape as `top_up`'s Stripe re-check, just against our own fake session
    state instead of Stripe's API. `stripe_payment_intent_id` doubles as the idempotency key here
    too (`khqr_<session_id>`, still unique) rather than adding a KHQR-specific column."""
    session = _khqr_sessions.get(session_id)
    if not session or session["user_id"] != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "KHQR session not found")
    if session["status"] != "confirmed":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment has not been confirmed yet")

    client = get_supabase_client()
    user = client.table("users").select("coin_balance").eq("id", user_id).maybe_single().execute()
    if not user or not user.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    try:
        _record_transaction(
            client,
            user_id,
            kind="topup",
            label="Top-up",
            detail="KHQR",
            coins=session["coins"],
            stripe_payment_intent_id=f"khqr_{session_id}",
        )
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This payment has already been used") from exc

    client.table("users").update({"coin_balance": user.data["coin_balance"] + session["coins"]}).eq(
        "id", user_id
    ).execute()
    del _khqr_sessions[session_id]

    return _get_wallet(user_id)


# Payout methods ------------------------------------------------------------------------------
# 4.29: these used to be read-only, with "+ Add payout method" a disabled stub on the Withdraw
# page and the Settings > Payments tab. That left a Pal with no seeded row unable to withdraw at
# all (the Withdraw button disables itself when the list is empty), so the flow now has a real
# create/default/delete trio, same shape as `routers/settings.py`'s payment cards.



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


@router.post("/payout-methods", response_model=PayoutMethodOut, status_code=status.HTTP_201_CREATED)
def create_payout_method(payload: PayoutMethodCreateIn, user_id: str = Depends(get_current_user_id)) -> dict:
    if payload.brand not in _PAYOUT_BRANDS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unsupported payout brand")
    digits = _digits(payload.account)
    if payload.brand == "card" and (not 12 <= len(digits) <= 19 or not _luhn_ok(digits)):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Enter a valid card number")
    if payload.brand == "bank" and len(digits) < 6:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Enter the full ABA account number")

    client = get_supabase_client()
    player = _get_owned_player(user_id)
    existing = (
        client.table("payout_methods").select("id").eq("player_id", player["id"]).execute().data or []
    )
    # The first method a Pal adds has to be the default - otherwise nothing is selected and the
    # Withdraw page is back to having no usable method.
    is_default = payload.is_default or not existing

    stored_brand, label, detail = _mask_account(payload.brand, payload.account)
    method_id = str(uuid4())
    if is_default:
        client.table("payout_methods").update({"is_default": False}).eq("player_id", player["id"]).execute()
    client.table("payout_methods").insert(
        {
            "id": method_id,
            "player_id": player["id"],
            "brand": stored_brand,
            "label": label,
            "detail": detail,
            "is_default": is_default,
        }
    ).execute()
    return _get_owned_payout_method(player["id"], method_id)


@router.patch("/payout-methods/{method_id}/default", response_model=PayoutMethodOut)
def set_default_payout_method(method_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    player = _get_owned_player(user_id)
    _get_owned_payout_method(player["id"], method_id)
    client = get_supabase_client()
    client.table("payout_methods").update({"is_default": False}).eq("player_id", player["id"]).execute()
    client.table("payout_methods").update({"is_default": True}).eq("id", method_id).execute()
    return _get_owned_payout_method(player["id"], method_id)


@router.delete("/payout-methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payout_method(method_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    """A withdrawal already in the queue keeps pointing at this row until the FK nulls it out
    (`on delete set null`), so the admin's Payouts tab falls back to "No payout method" rather
    than losing the request."""
    player = _get_owned_player(user_id)
    method = _get_owned_payout_method(player["id"], method_id)
    client = get_supabase_client()
    client.table("payout_methods").delete().eq("id", method_id).execute()

    # Promote the oldest remaining method so a Pal is never left with methods but no default.
    if method["is_default"]:
        remaining = (
            client.table("payout_methods")
            .select("id")
            .eq("player_id", player["id"])
            .order("created_at")
            .limit(1)
            .execute()
            .data
            or []
        )
        if remaining:
            client.table("payout_methods").update({"is_default": True}).eq("id", remaining[0]["id"]).execute()


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

    available = (
        user.data["coin_balance"]
        - _pending_clearance_coins(client, player["id"])
        - _locked_payout_coins(client, player["id"])
    )
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
            # 4.28b: a payout is a request, not a settlement - an admin approves or rejects it
            # from the Payouts tab before any money moves.
            "status": "requested",
            "reference": _payout_reference(),
        }
    ).execute()
    # 4.31: the balance is NOT debited here. The request only puts the coins on hold
    # (`_locked_payout_coins`); the debit lands when an admin approves, which is what makes the
    # approval feel like the moment the money leaves. The transaction row is logged now, as
    # `pending`, so the hold is visible in wallet activity while it waits.
    _record_transaction(
        client,
        user_id,
        kind="payout",
        label="Withdrawal",
        detail="Awaiting approval",
        coins=-payload.coins,
        txn_status="pending",
        withdrawal_id=withdrawal_id,
    )
    notify(user_id, "payout", f"Withdrawal of {payload.coins} SC requested. It's awaiting review.")

    return client.table("withdrawals").select("*").eq("id", withdrawal_id).single().execute().data
