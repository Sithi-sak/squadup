from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import get_current_user_id
from ..core.schema import CamelModel
from ..core.supabase import get_supabase_client

router = APIRouter(prefix="/users", tags=["users"])


class UserOut(CamelModel):
    id: str
    email: str
    display_name: str | None
    role: str
    onboarding_complete: bool
    coin_balance: int


class UserUpdateIn(CamelModel):
    display_name: str | None = None


def _fetch_user(user_id: str) -> dict:
    result = get_supabase_client().table("users").select("*").eq("id", user_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return result.data


@router.get("/me", response_model=UserOut)
def get_me(user_id: str = Depends(get_current_user_id)) -> dict:
    return _fetch_user(user_id)


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdateIn, user_id: str = Depends(get_current_user_id)) -> dict:
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        get_supabase_client().table("users").update(updates).eq("id", user_id).execute()
    return _fetch_user(user_id)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user_id: str = Depends(get_current_user_id)) -> None:
    # `auth.users` -> `public.users` -> `players` -> everything else cascades in one transaction
    # per the 3.13c migration, so no explicit pre-cleanup is needed here.
    get_supabase_client().auth.admin.delete_user(user_id)
