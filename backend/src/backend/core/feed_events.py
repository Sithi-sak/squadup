from uuid import uuid4

from .supabase import get_supabase_client


def post_status(user_id: str, text: str, category: str = "games") -> None:
    """Insert a system-authored `kind='status'` post for `user_id` - the auto-generated feed
    activity (booking completed, review left, new follower, Pal approved, ...) that keeps the
    Feed active without anyone opening the composer. Fire-and-forget, same convention as
    `notify()`."""
    get_supabase_client().table("posts").insert(
        {
            "id": str(uuid4()),
            "author_id": user_id,
            "text": text,
            "category": category,
            "kind": "status",
        }
    ).execute()
