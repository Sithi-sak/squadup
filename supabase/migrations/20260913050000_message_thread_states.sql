-- Per-user mute/delete state for message threads.
-- `message_threads` is one shared row per pair (2.3), but muting/deleting a chat is a
-- per-participant preference, not something the other side should see or be affected by - so
-- this is a separate row per (thread, user) rather than columns on `message_threads` itself.
-- Deleting is a soft hide (`deleted_at`) rather than removing the thread/messages, since the
-- other participant's copy of the conversation must survive it.

create table public.message_thread_states (
  thread_id uuid not null references public.message_threads (id) on delete cascade,
  user_id uuid not null references public.users (id) on delete cascade,
  muted boolean not null default false,
  deleted_at timestamptz,
  primary key (thread_id, user_id)
);

alter table public.message_thread_states enable row level security;
