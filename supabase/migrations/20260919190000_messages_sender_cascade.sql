-- `messages.sender_id` was the one FK into `public.users` that the 3.13c account-deletion
-- cascade (20260825141921) missed: it stayed `no action` from the 2.3 initial schema. The
-- assumption was that `messages.thread_id`'s cascade off `message_threads` would clear a
-- departing user's messages first, so `sender_id` would never be checked - it isn't reliable,
-- and deleting a real account failed with 23503 (`messages_sender_id_fkey` still referenced)
-- from both the SQL editor and `auth.admin.delete_user()` (routers/users.py's DELETE /users/me).
--
-- Same posture as every other edge in 3.13c: a hard delete walks the whole graph in one
-- transaction, including the counterparty's copy of the conversation.
alter table public.messages
  drop constraint messages_sender_id_fkey,
  add constraint messages_sender_id_fkey
    foreign key (sender_id) references public.users (id) on delete cascade;
