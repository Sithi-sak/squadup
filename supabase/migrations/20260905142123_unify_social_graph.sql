-- Unify the social graph (posts + follows) around `users` instead of `players`, so any account
-- (Pal or plain buyer) can post and be followed. `posts`/`follows` are both empty in the linked
-- project and every `players` row has a non-null `user_id`, so this is a direct, backfill-free
-- change. Services/bookings/reviews stay Pal-only (`players.id`), untouched here.

alter table public.users
  add column posts_count integer not null default 0,
  add column followers_count integer not null default 0,
  add column following_count integer not null default 0;

alter table public.posts
  add column author_id uuid not null references public.users (id) on delete cascade;

drop index public.posts_player_id_idx;
alter table public.posts drop column player_id;
create index posts_author_id_idx on public.posts (author_id);

alter table public.follows
  add column followed_id uuid not null references public.users (id) on delete cascade;

alter table public.follows drop constraint follows_pkey;
alter table public.follows drop column player_id;
alter table public.follows add primary key (follower_id, followed_id);
alter table public.follows add constraint follows_no_self_follow check (follower_id <> followed_id);

alter table public.players
  drop column posts_count,
  drop column followers_count,
  drop column following_count;
