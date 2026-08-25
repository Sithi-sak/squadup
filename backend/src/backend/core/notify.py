from .supabase import get_supabase_client


def notify(user_id: str, notif_type: str, message: str) -> None:
    """Insert a `notifications` row for `user_id` - shared by bookings/messages/reviews/wallet
    (3.10) so each event source doesn't duplicate the insert shape. Fire-and-forget: callers
    don't need the created row back, matching `wallet.py`'s `_record_transaction` convention."""
    get_supabase_client().table("notifications").insert(
        {"user_id": user_id, "type": notif_type, "message": message}
    ).execute()
