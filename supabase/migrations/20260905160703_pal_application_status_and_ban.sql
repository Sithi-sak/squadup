-- Pal application review (3.19): a new Pal Application no longer goes live instantly, it needs
-- admin approval. Existing rows default to 'approved' so seeded/live Pals are unaffected; new
-- signups are explicitly inserted as 'pending_review' by the backend.
create type pal_application_status as enum ('pending_review', 'approved', 'rejected');

alter table public.players
  add column status pal_application_status not null default 'approved',
  add column is_banned boolean not null default false;
