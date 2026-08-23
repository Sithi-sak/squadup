-- 2.3's `posts.likes_count`/`comments.likes_count` are plain counters with no table recording
-- *who* liked what, so there's no way to toggle a like or know a viewer's own liked state (3.8).
-- Two join tables, same shape as `follows`.

create table public.post_likes (
  user_id uuid not null references public.users (id) on delete cascade,
  post_id uuid not null references public.posts (id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, post_id)
);

create table public.comment_likes (
  user_id uuid not null references public.users (id) on delete cascade,
  comment_id uuid not null references public.comments (id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, comment_id)
);

-- Same RLS posture as every other 2.3 table: enabled, zero policies, service_role-only until a
-- feature needs otherwise (none of 3.8's reads need client-side Realtime, unlike 3.5b's messages).
alter table public.post_likes enable row level security;
alter table public.comment_likes enable row level security;
