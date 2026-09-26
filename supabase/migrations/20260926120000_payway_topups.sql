-- 4.57: ABA PayWay replaces Stripe for card top-ups.
--
-- One row per card top-up attempt, keyed by the `tran_id` PayWay knows it by. The coins and
-- price are frozen at checkout time, so a package edited mid-payment can't change what gets
-- credited. Written only by the backend's service-role client (`routers/wallet.py`), which flips
-- a row `pending` -> `paid` after PayWay's Check Transaction API confirms it, with a conditional
-- update so a poll and a callback racing each other credit it once.

create table public.payway_topups (
  tran_id text primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  package_id uuid references public.topup_packages (id) on delete set null,
  coins integer not null,
  amount_usd numeric(10, 2) not null,
  status text not null default 'pending' check (status in ('pending', 'paid')),
  created_at timestamptz not null default now(),
  paid_at timestamptz
);

create index payway_topups_user_id_idx on public.payway_topups (user_id, created_at desc);

alter table public.payway_topups enable row level security;

-- The idempotency key on a top-up's ledger row now holds `payway_<tran_id>` or
-- `khqr_<session_id>`, not a Stripe id. Same role and unique constraint, honest name.
alter table public.wallet_transactions
  rename column stripe_payment_intent_id to payment_reference;
