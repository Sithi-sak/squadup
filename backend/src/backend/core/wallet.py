from fastapi import HTTPException, status


def get_coin_balance(client, user_id: str) -> int:
    user = client.table("users").select("coin_balance").eq("id", user_id).maybe_single().execute()
    if not user or not user.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user.data["coin_balance"]


def adjust_coin_balance(
    client,
    user_id: str,
    delta: int,
    *,
    kind: str,
    label: str,
    detail: str | None = None,
    txn_status: str = "completed",
    booking_id: str | None = None,
) -> int:
    """Applies `delta` (negative to debit, positive to credit) to `user_id`'s `coin_balance` and
    logs a matching `wallet_transactions` row in one place - shared by the booking lifecycle
    (spend on create, earn on complete, refund on cancel/decline/dispute-resolution) so each
    event source doesn't duplicate the read-modify-write + audit-row shape (mirrors `notify()`'s
    role for notifications). Raises 409 rather than letting a balance go negative. Doesn't touch
    `routers/wallet.py`'s own topup/withdrawal read-modify-write - those rely on inserting the
    `wallet_transactions` row *before* crediting so a replayed Stripe `payment_intent_id`'s unique
    constraint blocks the credit, an ordering this helper doesn't need for booking events."""
    new_balance = get_coin_balance(client, user_id) + delta
    if new_balance < 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Insufficient Squad Coin balance")

    client.table("users").update({"coin_balance": new_balance}).eq("id", user_id).execute()
    client.table("wallet_transactions").insert(
        {
            "user_id": user_id,
            "kind": kind,
            "status": txn_status,
            "label": label,
            "detail": detail,
            "coins": delta,
            "booking_id": booking_id,
        }
    ).execute()
    return new_balance
