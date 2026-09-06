-- Unifies two disconnected handle concepts into one: `players.handle` (Pal-only, auto-generated
-- on Pal application) and Settings' Account tab "Username" field (never had a column to land in
-- at all - the input was pure local state that vanished on save). One `users.handle` now backs
-- both a Pal's marketplace handle and every account's own username.
alter table public.users
  add column handle text unique;

update public.users u
set handle = p.handle
from public.players p
where p.user_id = u.id and p.handle is not null;

alter table public.players
  drop column handle;
