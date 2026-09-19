-- 4.39: real blocking. "Also block" in the report modal and the Block menu item both claimed an
-- effect nothing implemented - there was no table, no endpoint and no enforcement anywhere.
--
-- One row per direction: `blocker_id` blocked `blocked_id`. Enforcement treats a block as mutual
-- (neither side can message, book or read the other's profile) but the row stays one-directional
-- so only the person who blocked can lift it.

create table public.user_blocks (
  id uuid primary key default gen_random_uuid(),
  blocker_id uuid not null references public.users (id) on delete cascade,
  blocked_id uuid not null references public.users (id) on delete cascade,
  created_at timestamptz not null default now(),
  constraint user_blocks_no_self check (blocker_id <> blocked_id),
  constraint user_blocks_unique unique (blocker_id, blocked_id)
);

create index user_blocks_blocker_id_idx on public.user_blocks (blocker_id);
create index user_blocks_blocked_id_idx on public.user_blocks (blocked_id);

-- Same posture as every other table: RLS on with no policies, so anon/authenticated get nothing
-- and the service-role backend keeps working.
alter table public.user_blocks enable row level security;
