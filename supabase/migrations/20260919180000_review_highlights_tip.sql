-- 4.44a: `LeaveReviewModal` has always collected "What went well?" chips and an optional tip,
-- and 3.6a dropped both on submit because `reviews` had nowhere to put them and tips needed the
-- wallet ledger. Both now land. `tip` is its own transaction kind so a tip reads as a tip in
-- Wallet history instead of masquerading as a second `order` line against the same booking.

alter type wallet_transaction_kind add value if not exists 'tip';

alter table public.reviews
  add column if not exists highlights text[] not null default '{}',
  add column if not exists tip_coins integer not null default 0;

alter table public.reviews
  drop constraint if exists reviews_tip_coins_check,
  add constraint reviews_tip_coins_check check (tip_coins >= 0);
