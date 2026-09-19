-- 4.28b (part 2): a new enum value cannot be used in the same transaction that adds it, so the
-- default flip lives in its own migration after `20260919120000_withdrawal_approval.sql`.

alter table public.withdrawals
  add column if not exists reviewed_at timestamptz;

alter table public.withdrawals
  alter column status set default 'requested';

create index if not exists withdrawals_status_idx on public.withdrawals (status);
