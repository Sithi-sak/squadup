-- Auto-generated "status" posts (booking completed, review left, new follower, Pal approved)
-- alongside manually composed posts, so the Feed stays active without anyone opening the
-- composer. `kind` distinguishes the two for `FeedPostCard.vue`'s compact status styling.
create type post_kind as enum ('user', 'status');

alter table public.posts
  add column kind post_kind not null default 'user';
