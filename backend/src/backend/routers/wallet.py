import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool

from ..core import payway
from ..core.auth import get_current_user_id
from ..core.notify import notify
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/wallet", tags=["wallet"])
logger = logging.getLogger(__name__)

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

# 4.59: the demo payout card (user request). Payouts are simulated - no money moves on approval
# (see `admin.update_withdrawal_status`) - and this number fails the Luhn check, so it is let
# through by name. Mirrors `utils/card.ts`.
_DEMO_PAYOUT_CARDS = {"5156839937706777"}

# A payout request that is still waiting on, or in the middle of, an admin decision. Its coins are
# held out of the withdrawable balance but not debited yet (4.31).
_OPEN_WITHDRAWAL_STATUSES = ("requested", "in_progress")

# 4.58: "QR Scan" shows a real ABA KHQR from PayWay, but a classroom demo can't count on someone
# actually paying it, so a KHQR top-up also auto-succeeds this many seconds after it was created.
# A real scan settles it the same way, just sooner. Card top-ups never auto-succeed.
KHQR_AUTO_CONFIRM_SECONDS = 10

_TOPUP_DETAIL = {"card": "Card", "khqr": "KHQR"}


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


class TopupPackageIn(CamelModel):
    package_id: str


class CardCheckoutOut(CamelModel):
    tran_id: str
    amount_usd: float
    # Signed fields for PayWay's card popup, posted by the browser itself (`lib/payway.ts`).
    form: dict[str, str]


class KhqrCheckoutOut(CamelModel):
    tran_id: str
    amount_usd: float
    coins: int
    # The KHQR string itself; `KhqrCard.vue` draws the code from it.
    qr_string: str
    expires_at: str


class TopupStatusOut(CamelModel):
    # 'pending' | 'paid' | 'failed' | 'expired' ('expired' is KHQR only)
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
    payment_reference: str | None = None,
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
            "payment_reference": payment_reference,
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


def _get_package(client, package_id: str) -> dict:
    package = client.table("topup_packages").select("*").eq("id", package_id).maybe_single().execute()
    if not package or not package.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Top-up package not found")
    return package.data


def _credit_topup(client, user_id: str, *, coins: int, detail: str, payment_reference: str) -> None:
    """Logs the ledger row *before* crediting, so the unique `payment_reference` rejects a second
    credit for the same payment before the balance moves."""
    user = client.table("users").select("coin_balance").eq("id", user_id).maybe_single().execute()
    if not user or not user.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    try:
        _record_transaction(
            client,
            user_id,
            kind="topup",
            label="Top-up",
            detail=detail,
            coins=coins,
            payment_reference=payment_reference,
        )
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This payment has already been used") from exc
    client.table("users").update({"coin_balance": user.data["coin_balance"] + coins}).eq("id", user_id).execute()


def _settle_topup(topup: dict) -> str:
    """'paid', 'pending', 'failed' or 'expired' for a PayWay top-up, crediting it the first time
    it's settled (4.57c/4.58b). Only PayWay's signed Check Transaction answer counts as a real
    payment - never the client's or a callback body's word that it went through. The one
    exception is the KHQR demo timer (`KHQR_AUTO_CONFIRM_SECONDS`)."""
    if topup["status"] == "paid":
        return "paid"

    approved = False
    result = payway.check_transaction(topup["tran_id"])
    if result:
        payment_status = result.get("payment_status")
        if payment_status in payway.FAILED_STATUSES:
            return "failed"
        if payment_status == payway.APPROVED:
            # Guards against a transaction for some other amount being passed off under this
            # tran_id.
            if abs(float(result.get("total_amount", 0)) - float(topup["amount_usd"])) > 0.005:
                logger.error(
                    "tran=%s approved amount %s != expected %s",
                    topup["tran_id"],
                    result.get("total_amount"),
                    topup["amount_usd"],
                )
                return "failed"
            approved = True

    if not approved and topup["method"] == "khqr":
        age = datetime.now(UTC) - datetime.fromisoformat(topup["created_at"])
        if age >= timedelta(minutes=payway.QR_LIFETIME_MINUTES):
            return "expired"
        if age >= timedelta(seconds=KHQR_AUTO_CONFIRM_SECONDS):
            logger.info("tran=%s KHQR demo auto-confirm", topup["tran_id"])
            approved = True

    if not approved:
        return "pending"

    # Only the request that flips the row out of 'pending' credits it, so a poll and a callback
    # racing each other can't both add the coins.
    client = get_supabase_client()
    claimed = (
        client.table("payway_topups")
        .update({"status": "paid", "paid_at": datetime.now(UTC).isoformat()})
        .eq("tran_id", topup["tran_id"])
        .eq("status", "pending")
        .execute()
    )
    if claimed.data:
        _credit_topup(
            client,
            topup["user_id"],
            coins=topup["coins"],
            detail=_TOPUP_DETAIL[topup["method"]],
            payment_reference=f"payway_{topup['tran_id']}",
        )
    return "paid"


def _get_topup(tran_id: str) -> dict | None:
    rows = get_supabase_client().table("payway_topups").select("*").eq("tran_id", tran_id).execute().data
    return rows[0] if rows else None


def _get_owned_topup(tran_id: str, user_id: str, method: str) -> dict:
    topup = _get_topup(tran_id)
    if not topup or topup["user_id"] != user_id or topup["method"] != method:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Top-up not found")
    return topup


def _start_topup(client, user_id: str, package_id: str, method: str) -> tuple[dict, str, str]:
    """Records a pending `payway_topups` row for the package, freezing its coins and price, and
    returns `(row, tran_id, payer_email)`."""
    package = _get_package(client, package_id)
    user = client.table("users").select("email").eq("id", user_id).maybe_single().execute()
    if not user or not user.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    row = {
        "tran_id": payway.new_tran_id(),
        "user_id": user_id,
        "package_id": package["id"],
        "method": method,
        "coins": package["coins"] + package["bonus_coins"],
        "amount_usd": float(package["price_usd"]),
    }
    client.table("payway_topups").insert(row).execute()
    return row, row["tran_id"], user.data["email"]


def _topup_description(coins: int) -> str:
    return f"SquadUp {coins:,} Squad Coin"


@router.post("/topup/card", response_model=CardCheckoutOut, status_code=status.HTTP_201_CREATED)
def create_card_checkout(payload: TopupPackageIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """4.57c: records a pending card top-up and returns the signed fields for PayWay's card
    popup. Nothing is credited here - the popup charges the card on PayWay's side, and
    `GET /topup/card/{tran_id}` (or PayWay's callback) settles it afterwards."""
    row, tran_id, email = _start_topup(get_supabase_client(), user_id, payload.package_id, "card")
    form = payway.card_checkout_form(tran_id, row["amount_usd"], _topup_description(row["coins"]), email)
    return {"tran_id": tran_id, "amount_usd": row["amount_usd"], "form": form}


@router.get("/topup/card/{tran_id}", response_model=TopupStatusOut)
def get_card_topup_status(tran_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    """Polled by the Wallet page while PayWay's popup is up. Settles the top-up as a side effect,
    so local dev (where PayWay's callback can't reach localhost) works without the callback."""
    return {"status": _settle_topup(_get_owned_topup(tran_id, user_id, "card"))}


@router.post("/topup/khqr", response_model=KhqrCheckoutOut, status_code=status.HTTP_201_CREATED)
def create_khqr_checkout(payload: TopupPackageIn, user_id: str = Depends(get_current_user_id)) -> dict:
    """4.58b: records a pending KHQR top-up and asks PayWay for a real KHQR for it, payable from
    ABA Mobile or any Bakong member bank app until `expires_at`."""
    client = get_supabase_client()
    row, tran_id, email = _start_topup(client, user_id, payload.package_id, "khqr")
    try:
        qr_string = payway.generate_qr(tran_id, row["amount_usd"], _topup_description(row["coins"]), email)
    except payway.PayWayError as exc:
        logger.exception("user=%s KHQR generation failed", user_id)
        client.table("payway_topups").delete().eq("tran_id", tran_id).execute()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not create a KHQR payment") from exc

    expires_at = datetime.now(UTC) + timedelta(minutes=payway.QR_LIFETIME_MINUTES)
    return {
        "tran_id": tran_id,
        "amount_usd": row["amount_usd"],
        "coins": row["coins"],
        "qr_string": qr_string,
        "expires_at": expires_at.isoformat(),
    }


@router.get("/topup/khqr/{tran_id}", response_model=TopupStatusOut)
def get_khqr_topup_status(tran_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    """Polled while the KHQR modal is open. Settles on a real PayWay payment or, for the demo,
    once `KHQR_AUTO_CONFIRM_SECONDS` have passed."""
    return {"status": _settle_topup(_get_owned_topup(tran_id, user_id, "khqr"))}


@router.post("/topup/payway/callback")
async def payway_callback(request: Request) -> dict[str, bool]:
    """PayWay's pushback once a card or KHQR payment completes. Public on purpose; the body is
    only used to find the row, and `_settle_topup` re-checks with PayWay before crediting
    anything, so a forged callback can't mint coins."""
    try:
        body = await request.json()
    except ValueError:
        body = dict(await request.form())
    tran_id = body.get("tran_id")
    topup = await run_in_threadpool(_get_topup, tran_id) if isinstance(tran_id, str) else None
    if topup:
        await run_in_threadpool(_settle_topup, topup)
    return {"received": True}


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
    if (
        payload.brand == "card"
        and digits not in _DEMO_PAYOUT_CARDS
        and (not 12 <= len(digits) <= 19 or not _luhn_ok(digits))
    ):
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
