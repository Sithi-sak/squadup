-- Live header balance (CHECKPOINT.md 4.74a).
-- The wallet store subscribes to `UPDATE`s on the signed-in user's own `users` row so
-- `coin_balance` changes (order earnings, refunds, top-ups, payouts) reach the header without a
-- reload. Realtime authorizes each event against the RLS a SELECT would see, and
-- "Users can view their own row" (20260822073236_auth_wiring.sql) already limits that to the
-- owner. Every balance write still goes through the service-role backend (`core/wallet.py`,
-- `routers/wallet.py`, `routers/admin.py`), which bypasses RLS.

alter publication supabase_realtime add table public.users;
