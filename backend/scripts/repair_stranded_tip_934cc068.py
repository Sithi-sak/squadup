"""One-off repair for the 4.53 tip that went missing on 2026-09-20.

Booking 934cc068's review committed and took 200 SC off the buyer, then the connection dropped
before the Pal's side of the tip was written, so the coins exist nowhere. The 4.53 migration
stops this happening again but can't recover what was already lost.

Credits the Pal the missing 200 SC and writes the `wallet_transactions` row the crashed request
would have written. Safe to run twice: it exits if the Pal's tip row already exists.

    cd backend && .venv/bin/python scripts/repair_stranded_tip_934cc068.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from backend.core.supabase import get_supabase_client

BOOKING_ID = "934cc068-b749-406f-8b0f-3ec0e4e50542"
PAL_USER_ID = "429a6293-6c88-40e7-be45-92f0468a05ef"  # Lucid
COINS = 200
DETAIL = "From Levi"


def main() -> None:
    client = get_supabase_client()

    already = (
        client.table("wallet_transactions")
        .select("id")
        .eq("booking_id", BOOKING_ID)
        .eq("user_id", PAL_USER_ID)
        .eq("kind", "tip")
        .execute()
        .data
    )
    if already:
        print(f"Already repaired - the Pal's tip row exists ({already[0]['id']}). Nothing to do.")
        return

    before = client.table("users").select("coin_balance").eq("id", PAL_USER_ID).single().execute().data[
        "coin_balance"
    ]
    client.table("users").update({"coin_balance": before + COINS}).eq("id", PAL_USER_ID).execute()
    client.table("wallet_transactions").insert(
        {
            "user_id": PAL_USER_ID,
            "kind": "tip",
            "status": "completed",
            "label": "Tip",
            "detail": DETAIL,
            "coins": COINS,
            "booking_id": BOOKING_ID,
        }
    ).execute()

    after = client.table("users").select("coin_balance").eq("id", PAL_USER_ID).single().execute().data[
        "coin_balance"
    ]
    print(f"Credited {COINS} SC to the Pal: {before} -> {after}")


if __name__ == "__main__":
    main()
