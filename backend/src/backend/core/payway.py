"""ABA PayWay client (4.57/4.58) - request signing plus the endpoints card and KHQR top-ups need.

Ported from Niyey's PayWay checkout. Every PayWay request carries a `hash`: base64
HMAC-SHA512, keyed with the merchant's API key, over a fixed list of fields concatenated in the
order each endpoint's docs give (empty string for any optional field left out). The order differs
per endpoint, so each builder below spells its own out.
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import UTC, datetime

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)

PURCHASE_PATH = "/api/payment-gateway/v1/payments/purchase"
GENERATE_QR_PATH = "/api/payment-gateway/v1/payments/generate-qr"
CHECK_TRANSACTION_PATH = "/api/payment-gateway/v1/payments/check-transaction-2"

# Minutes a KHQR stays payable. PayWay's floor is 3; a payment that lands after this is rejected
# and reversed to the payer by PayWay itself.
QR_LIFETIME_MINUTES = 5

# PayWay's `payment_status` values that mean the money actually moved, or never will.
APPROVED = "APPROVED"
FAILED_STATUSES = {"DECLINED", "CANCELLED", "REFUNDED"}


class PayWayError(Exception):
    pass


def _sign(*values: str) -> str:
    digest = hmac.new(get_settings().payway_api_key.encode(), "".join(values).encode(), hashlib.sha512).digest()
    return base64.b64encode(digest).decode()


def _b64(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


def _req_time() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


def new_tran_id() -> str:
    """Unique per attempt and within PayWay's 20-character limit."""
    return f"SU{int(time.time() * 1000):x}{secrets.token_hex(2)}".upper()


def format_amount(amount: float) -> str:
    """The hashed amount has to be byte-identical to the one sent, so both go through this."""
    return f"{amount:.2f}"


def _items(description: str, amount_text: str) -> str:
    return _b64(json.dumps([{"name": description, "quantity": 1, "price": float(amount_text)}]))


def card_checkout_form(tran_id: str, amount: float, description: str, email: str) -> dict[str, str]:
    """Signed fields for the Purchase API's card popup.

    The browser posts these itself through PayWay's `checkout2-0.js` plugin (it renders the card
    form in an iframe), so this only builds and signs them. `payment_gate=0` routes the request to
    Ecommerce Checkout rather than the QR API, which the same endpoint otherwise defaults to on a
    profile that has both; it isn't part of the hash.

    `skip_success_page=1` with no `continue_success_url` makes the plugin just close the popup
    once the card is charged, so the Wallet page's own polling takes over.
    """
    settings = get_settings()
    amount_text = format_amount(amount)
    items = _items(description, amount_text)
    fields = {
        "req_time": _req_time(),
        "merchant_id": settings.payway_merchant_id,
        "tran_id": tran_id,
        "amount": amount_text,
        "items": items,
        "email": email,
        "payment_option": "cards",
        "return_url": _b64(settings.payway_callback_url) if settings.payway_callback_url else "",
        "currency": "USD",
        "skip_success_page": "1",
    }
    fields["hash"] = _sign(
        fields["req_time"],
        fields["merchant_id"],
        fields["tran_id"],
        fields["amount"],
        fields["items"],
        "",  # shipping
        "",  # firstname
        "",  # lastname
        fields["email"],
        "",  # phone
        "",  # type
        fields["payment_option"],
        fields["return_url"],
        "",  # cancel_url
        "",  # continue_success_url
        "",  # return_deeplink
        fields["currency"],
        "",  # custom_fields
        "",  # return_params
        "",  # payout
        "",  # lifetime
        "",  # additional_params
        "",  # google_pay_token
        fields["skip_success_page"],
    )
    fields["payment_gate"] = "0"
    fields["form_url"] = settings.payway_base_url + PURCHASE_PATH
    return {key: value for key, value in fields.items() if value != ""}


def generate_qr(tran_id: str, amount: float, description: str, email: str) -> str:
    """ABA QR API (4.58) - a dynamic KHQR string any Bakong member bank app can pay. The frontend
    renders it itself (`components/wallet/KhqrCard.vue`), so only the string is returned."""
    settings = get_settings()
    amount_text = format_amount(amount)
    items = _items(description, amount_text)
    callback_url = _b64(settings.payway_callback_url) if settings.payway_callback_url else ""
    body: dict[str, object] = {
        "req_time": _req_time(),
        "merchant_id": settings.payway_merchant_id,
        "tran_id": tran_id,
        # Sent as the same string that's hashed. As a JSON number, a whole-dollar price like 10.0
        # reaches PayWay as something other than "10.00" and fails with "Wrong Hash."
        "amount": amount_text,
        "items": items,
        "email": email,
        "payment_option": "abapay_khqr",
        "callback_url": callback_url,
        "currency": "USD",
        "lifetime": QR_LIFETIME_MINUTES,
        "qr_image_template": "template3_color",
    }
    body["hash"] = _sign(
        str(body["req_time"]),
        settings.payway_merchant_id,
        tran_id,
        amount_text,
        items,
        "",  # first_name
        "",  # last_name
        email,
        "",  # phone
        "",  # purchase_type
        "abapay_khqr",
        callback_url,
        "",  # return_deeplink
        "USD",
        "",  # custom_fields
        "",  # return_params
        "",  # payout
        str(QR_LIFETIME_MINUTES),
        "template3_color",
    )
    body = {key: value for key, value in body.items() if value != ""}

    try:
        data = httpx.post(settings.payway_base_url + GENERATE_QR_PATH, json=body, timeout=30).json()
    except (httpx.HTTPError, ValueError) as exc:
        raise PayWayError("generate-qr request failed") from exc
    status = data.get("status", {})
    if str(status.get("code")) != "0" or not data.get("qrString"):
        raise PayWayError(f"generate-qr failed: {status}")
    return data["qrString"]


def check_transaction(tran_id: str) -> dict | None:
    """The transaction's current state, or None if PayWay has no record of it (yet).

    This, not a callback body, is what a top-up is settled on: it's a signed request from us to
    PayWay, so its answer can't be forged by whoever happens to POST to the callback URL.
    """
    settings = get_settings()
    body = {"req_time": _req_time(), "merchant_id": settings.payway_merchant_id, "tran_id": tran_id}
    body["hash"] = _sign(body["req_time"], body["merchant_id"], tran_id)
    try:
        response = httpx.post(settings.payway_base_url + CHECK_TRANSACTION_PATH, json=body, timeout=30)
        data = response.json()
    except (httpx.HTTPError, ValueError):
        logger.exception("check-transaction tran=%s request failed", tran_id)
        return None
    status = data.get("status", {})
    if str(status.get("code")) != "00":
        # "wrong hash" here means PAYWAY_API_KEY/PAYWAY_MERCHANT_ID don't match the PayWay
        # profile; "not found" is normal for a payment not made yet.
        logger.warning("check-transaction tran=%s HTTP %s: %s", tran_id, response.status_code, status)
        return None
    return data.get("data")
