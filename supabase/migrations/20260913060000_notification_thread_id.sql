-- Lets a "message" notification deep-link back to its conversation (frontend clicks it to open
-- that thread). Nullable and `on delete set null` since every other notification type has no
-- thread, and a notification should outlive the thread if that ever gets hard-deleted.

alter table public.notifications
  add column thread_id uuid references public.message_threads (id) on delete set null;
