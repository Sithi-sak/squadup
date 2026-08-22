from fastapi import Header, HTTPException, status

from .supabase import get_supabase_client


def _resolve_user_id(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        response = get_supabase_client().auth.get_user(token)
    except Exception:  # noqa: BLE001 - any failure just means "not authenticated"
        return None
    return response.user.id if response and response.user else None


def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    user_id = _resolve_user_id(authorization)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user_id
