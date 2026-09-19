-- 4.28d: a withdrawal request logs a `pending` payout row in `wallet_transactions`, and the
-- admin's approve/reject has to settle that exact row. Matching it back by
-- user + kind + coins is ambiguous once a Pal has two same-sized requests open, so the
-- transaction now points at its withdrawal directly (same shape as the existing `booking_id`).

alter table public.wallet_transactions
  add column if not exists withdrawal_id uuid references public.withdrawals (id) on delete set null;
