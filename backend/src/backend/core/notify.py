from .supabase import get_supabase_client


def notify(
    user_id: str,
    notif_type: str,
    message: str,
    thread_id: str | None = None,
    booking_id: str | None = None,
) -> None:
    """Insert a `notifications` row for `user_id` - shared by bookings/messages/reviews/wallet
    (3.10) so each event source doesn't duplicate the insert shape. Fire-and-forget: callers
    don't need the created row back, matching `wallet.py`'s `_record_transaction` convention.
    `thread_id` lets a "message" notification deep-link back to its conversation, and
    `booking_id` lets a "booking" one open its order (4.69b)."""
    row: dict[str, str] = {"user_id": user_id, "type": notif_type, "message": message}
    if thread_id is not None:
        row["thread_id"] = thread_id
    if booking_id is not None:
        row["booking_id"] = booking_id
    get_supabase_client().table("notifications").insert(row).execute()
