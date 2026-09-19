-- 4.31: payouts are a simulation - no money actually moves - so the details that make one read as
-- real have to be in our own data. A short human reference is what a Pal would quote when asking
-- "where is my payout", and what the admin queue can be searched by.

alter table public.withdrawals
  add column if not exists reference text;

create unique index if not exists withdrawals_reference_key on public.withdrawals (reference);
