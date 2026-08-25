-- Account deletion cascade (CHECKPOINT.md 3.13c).
-- Fixes the gap flagged in 3.1e: deleting an auth.users row cascades to public.users (2.3's
-- `on delete cascade`) but stopped there — `players.user_id` was `on delete set null` (orphaning
-- the Pal profile instead of removing it) and every other edge from `players`/`users` into
-- bookings/subscriptions/withdrawals/message_threads/reviews/comments/order_cancellations/
-- order_disputes had no `on delete` action at all (NO ACTION), which would block
-- `auth.admin.delete_user()` outright the moment any of those rows existed. Re-pointing every one
-- of those FKs at `on delete cascade` makes a single `delete_user()` call (routers/users.py's
-- `DELETE /users/me`) walk the whole graph in one transaction, so 3.13c needs no explicit Python
-- pre-cleanup. `admin_flags.reported_by` gets `set null` instead since it's nullable and a flag
-- against a *different* player should survive the reporter deleting their own account.
--
-- Accepted tradeoff: this also removes bookings/reviews/messages/subscriptions/disputes the
-- deleted account was party to, including the counterparty's copy of that history — there's no
-- soft-delete/anonymization layer in this schema, and a hard delete is what "Delete Account"
-- promises in the Settings copy.

alter table public.players
  drop constraint players_user_id_fkey,
  add constraint players_user_id_fkey
    foreign key (user_id) references public.users (id) on delete cascade;

alter table public.bookings
  drop constraint bookings_player_id_fkey,
  add constraint bookings_player_id_fkey
    foreign key (player_id) references public.players (id) on delete cascade,
  drop constraint bookings_service_id_fkey,
  add constraint bookings_service_id_fkey
    foreign key (service_id) references public.services (id) on delete cascade,
  drop constraint bookings_user_id_fkey,
  add constraint bookings_user_id_fkey
    foreign key (user_id) references public.users (id) on delete cascade;

alter table public.subscriptions
  drop constraint subscriptions_player_id_fkey,
  add constraint subscriptions_player_id_fkey
    foreign key (player_id) references public.players (id) on delete cascade,
  drop constraint subscriptions_user_id_fkey,
  add constraint subscriptions_user_id_fkey
    foreign key (user_id) references public.users (id) on delete cascade;

alter table public.withdrawals
  drop constraint withdrawals_player_id_fkey,
  add constraint withdrawals_player_id_fkey
    foreign key (player_id) references public.players (id) on delete cascade;

alter table public.message_threads
  drop constraint message_threads_user_a_id_fkey,
  add constraint message_threads_user_a_id_fkey
    foreign key (user_a_id) references public.users (id) on delete cascade,
  drop constraint message_threads_user_b_id_fkey,
  add constraint message_threads_user_b_id_fkey
    foreign key (user_b_id) references public.users (id) on delete cascade;

alter table public.reviews
  drop constraint reviews_author_id_fkey,
  add constraint reviews_author_id_fkey
    foreign key (author_id) references public.users (id) on delete cascade;

alter table public.comments
  drop constraint comments_author_id_fkey,
  add constraint comments_author_id_fkey
    foreign key (author_id) references public.users (id) on delete cascade;

alter table public.order_cancellations
  drop constraint order_cancellations_cancelled_by_fkey,
  add constraint order_cancellations_cancelled_by_fkey
    foreign key (cancelled_by) references public.users (id) on delete cascade;

alter table public.order_disputes
  drop constraint order_disputes_reported_by_fkey,
  add constraint order_disputes_reported_by_fkey
    foreign key (reported_by) references public.users (id) on delete cascade;

alter table public.admin_flags
  drop constraint admin_flags_reported_by_fkey,
  add constraint admin_flags_reported_by_fkey
    foreign key (reported_by) references public.users (id) on delete set null;
