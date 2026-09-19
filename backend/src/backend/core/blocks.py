from fastapi import HTTPException, status

from .supabase import get_supabase_client


def blocked_user_ids(user_id: str | None) -> set[str]:
    """Every account `user_id` can't interact with: the ones they blocked and the ones who
    blocked them. A block is stored one-directional (only the blocker can lift it) but enforced
    both ways, so feeds, threads and profile reads all filter on this single set."""
    if not user_id:
        return set()
    client = get_supabase_client()
    rows = (
        client.table("user_blocks")
        .select("blocker_id, blocked_id")
        .or_(f"blocker_id.eq.{user_id},blocked_id.eq.{user_id}")
        .execute()
        .data
        or []
    )
    ids = {row["blocker_id"] for row in rows} | {row["blocked_id"] for row in rows}
    ids.discard(user_id)
    return ids


def has_blocked(blocker_id: str | None, blocked_id: str | None) -> bool:
    """Whether `blocker_id` is the one who blocked `blocked_id`. Direction matters for reads:
    the person who blocked keeps seeing the profile (that is where Unblock lives), while the
    person they blocked is the one shut out."""
    if not blocker_id or not blocked_id or blocker_id == blocked_id:
        return False
    rows = (
        get_supabase_client()
        .table("user_blocks")
        .select("id")
        .eq("blocker_id", blocker_id)
        .eq("blocked_id", blocked_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    return bool(rows)


def is_blocked_between(a_user_id: str | None, b_user_id: str | None) -> bool:
    """Whether a block exists in either direction between two accounts."""
    if not a_user_id or not b_user_id or a_user_id == b_user_id:
        return False
    rows = (
        get_supabase_client()
        .table("user_blocks")
        .select("id")
        .or_(
            f"and(blocker_id.eq.{a_user_id},blocked_id.eq.{b_user_id}),"
            f"and(blocker_id.eq.{b_user_id},blocked_id.eq.{a_user_id})"
        )
        .limit(1)
        .execute()
        .data
        or []
    )
    return bool(rows)


def require_not_blocked(a_user_id: str | None, b_user_id: str | None, action: str) -> None:
    """Guard for the write paths a block is supposed to stop (message, book). 403 rather than
    404: the two accounts already know about each other, and hiding the reason would just read
    as a bug to whoever hits it."""
    if is_blocked_between(a_user_id, b_user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"You can't {action} this account.")
