-- Manual platform commission tracking (CHECKPOINT 4.3) - recorded per booking once it
-- completes, no coins actually move for it (no escrow yet, see CHECKPOINT 4.5).
alter table public.bookings
  add column commission_pct numeric not null default 0,
  add column commission_coins integer not null default 0;
